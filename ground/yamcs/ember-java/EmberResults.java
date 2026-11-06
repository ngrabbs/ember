package com.example.ember;

import java.nio.ByteBuffer;
import java.util.HashMap;
import java.util.Map;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.Arrays;
import java.util.HexFormat;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import org.yamcs.cmdhistory.CommandHistoryPublisher;
import org.yamcs.cmdhistory.CommandHistoryPublisher.AckStatus;
import org.yamcs.protobuf.Commanding.CommandId;
import org.yamcs.utils.TimeEncoding;

/** Correlate validated result packets; timeout remains unknown, never retry. */
public final class EmberResults {
    private static final Map<String, EmberResults> INSTANCES = new ConcurrentHashMap<>();
    public static EmberResults forInstance(String instance) {
        return INSTANCES.computeIfAbsent(instance, key -> new EmberResults());
    }
    private static final int SET_HEARTBEAT = 7;
    private static final int SET_UHF_TELEMETRY_SCHEDULE = 8;
    private static final int SET_UHF_TELEMETRY = 9;
    private static final int SET_UHF_TELEMETRY_SET = 10;
    private static String payloadErrorName(long code) {
        if (code > 255) return "UNRECOGNIZED_PAYLOAD_ERROR";
        return switch ((int) code) {
            case 0 -> "NO_PAYLOAD_ERROR_REPORTED";
            case 1 -> "UNSUPPORTED_CAN_VERSION";
            case 2 -> "UNSUPPORTED_PAYLOAD_COMMAND";
            case 3 -> "SENDER_OR_SESSION_MISMATCH";
            case 4 -> "INVALID_CAN_PAYLOAD";
            case 5 -> "CAPTURE_BUSY";
            case 8 -> "CAPTURE_OR_EVIDENCE_ERROR";
            case 11 -> "ANALYSIS_NO_DECISION";
            default -> "UNRECOGNIZED_PAYLOAD_ERROR";
        };
    }

    private static final class Pending {
        CommandId id;
        CommandHistoryPublisher history;
        int command, parameter;
        long value, deadline, idleBeforeDispatchMs;
        boolean accepted;
        long started;
    }
    private final Map<String, Pending> pending = new HashMap<>();
    private long boot, lastObserved, baselineBoot, baselineCapture;
    private byte[] capturedBaseline;

    private EmberResults() {
        var timer = Executors.newSingleThreadScheduledExecutor(task -> {
            var thread = new Thread(task, "ember-result-timeouts");
            thread.setDaemon(true);
            return thread;
        });
        timer.scheduleAtFixedRate(this::expire, 100, 100, TimeUnit.MILLISECONDS);
    }
    private static String key(ByteBuffer b) {
        return Integer.toUnsignedLong(b.getInt(WireProfile.TRANSACTION_EPOCH)) + ":" +
               Integer.toUnsignedLong(b.getInt(WireProfile.TRANSACTION_ID));
    }
    public synchronized void register(CommandId id, CommandHistoryPublisher history, byte[] bytes) {
        if (pending.size() >= 256) throw new IllegalStateException("Too many outstanding EMBER bench commands");
        ByteBuffer b = ByteBuffer.wrap(bytes);
        Pending command = new Pending();
        command.id = id;
        command.history = history;
        command.command = Short.toUnsignedInt(b.getShort(WireProfile.MESSAGE_ID));
        if (command.command == 0x30) {
            command.parameter = Short.toUnsignedInt(b.getShort(WireProfile.SET_PARAMETER_PARAMETER_ID));
            command.value = Integer.toUnsignedLong(b.getInt(WireProfile.SET_PARAMETER_VALUE));
        }
        if(command.command==3) command.parameter=Byte.toUnsignedInt(b.get(30));
        if(command.command==SET_HEARTBEAT || command.command==SET_UHF_TELEMETRY ||
           command.command==SET_UHF_TELEMETRY_SET)
            command.value=Byte.toUnsignedInt(b.get(30));
        if(command.command==SET_UHF_TELEMETRY_SCHEDULE)
            command.value=Integer.toUnsignedLong(b.getInt(30));
        if(command.command==5) command.value=Integer.toUnsignedLong(b.getInt(30));
        command.started = System.nanoTime();
        command.idleBeforeDispatchMs=pending.isEmpty() && lastObserved!=0 ? (command.started-lastObserved)/1000000 : -1;
        command.deadline = command.started + TimeUnit.SECONDS.toNanos(command.command == 1028 || command.command == 1 || (command.command >= 2 && command.command <= SET_UHF_TELEMETRY_SET) ? 40 : 5);
        pending.put(key(b), command);
        history.publishAck(id, "Acknowledge_EMBER_Acceptance", TimeEncoding.getWallclockTime(), AckStatus.PENDING);
        history.publishAck(id, CommandHistoryPublisher.CommandComplete_KEY, TimeEncoding.getWallclockTime(), AckStatus.PENDING);
    }
    private void unknown(Pending command, String reason) {
        long now = TimeEncoding.getWallclockTime();
        if (!command.accepted) command.history.publishAck(command.id, "Acknowledge_EMBER_Acceptance", now, AckStatus.TIMEOUT, reason);
        command.history.publish(command.id, "ember-outcome", "UNKNOWN");
        command.history.publish(command.id, "ember-elapsed-ms", Long.toString((System.nanoTime()-command.started)/1000000));
        command.history.publishAck(command.id, CommandHistoryPublisher.CommandComplete_KEY, now, AckStatus.TIMEOUT, reason);
    }
    private synchronized void expire() {
        long now = System.nanoTime();
        pending.values().removeIf(command -> {
            if (now < command.deadline) return false;
            unknown(command, "Unknown outcome: EMBER result deadline expired; no automatic retry");
            return true;
        });
    }
    public synchronized void observe(byte[] bytes) {
        ByteBuffer b = ByteBuffer.wrap(bytes);
        int source = Byte.toUnsignedInt(b.get(WireProfile.SOURCE));
        if (source != 2) return;
        // A host-wrapped EPS observation uses the bridge's session as its boot.
        // It is telemetry provenance, never evidence that the physical IHU reset.
        if (Short.toUnsignedInt(b.getShort(WireProfile.MESSAGE_ID)) == 0x10 &&
            Byte.toUnsignedInt(b.get(WireProfile.POWER_STATUS_PROVENANCE)) != 2) return;
        long currentBoot = Integer.toUnsignedLong(b.getInt(WireProfile.SOURCE_BOOT_ID));
        if (boot != 0 && boot != currentBoot) {
            // A fresh, correlated read-only response can establish the new boot.
            // Other outstanding work remains uncertain across the reset.
            String currentKey=key(b);
            pending.entrySet().removeIf(entry -> {
                Pending x=entry.getValue();
                if(entry.getKey().equals(currentKey) && (x.command==1 || x.command==2 || x.command==3 || x.command==5))return false;
                unknown(x,"Unknown outcome: IHU boot identity changed");return true;
            });
        }
        boot = currentBoot;
        lastObserved=System.nanoTime();
        if (Byte.toUnsignedInt(b.get(WireProfile.KIND)) == 1 &&
            Short.toUnsignedInt(b.getShort(WireProfile.MESSAGE_ID)) == 59) {
            Pending records=pending.get(key(b));
            if(records==null || (records.command!=4 && records.command!=5) || bytes.length!=120 ||
                b.get(30)!=1 || b.get(31)!=5 || b.get(32)!=16 || b.get(33)!=1 || b.getInt(34)==0 ||
                (records.command==5 && records.value!=Integer.toUnsignedLong(b.getInt(34))))return;
            StringBuilder intervals=new StringBuilder();
            for(int i=0;i<5;i++){
                int offset=38+16*i;
                if(Short.toUnsignedInt(b.getShort(offset))!=i+1 || Byte.toUnsignedInt(b.get(offset+6))>4 ||
                    (b.get(offset+7)!=1 && b.get(offset+7)!=2) || Byte.toUnsignedInt(b.get(offset+9))>1 ||
                    Byte.toUnsignedInt(b.get(offset+11))>1)return;
                if(i>0){long dt=Integer.toUnsignedLong(b.getInt(offset+2)-b.getInt(offset-14));
                    if(dt<900 || dt>1100)return;
                    if(i>1)intervals.append(",");intervals.append(dt);
                }
            }
            String digest;
            try {digest=HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Arrays.copyOfRange(bytes,38,118)));}
            catch(NoSuchAlgorithmException impossible){throw new IllegalStateException(impossible);}
            long now=TimeEncoding.getWallclockTime();
            records.history.publish(records.id,"ember-outcome","COMPLETED");
            records.history.publish(records.id,"ember-elapsed-ms",Long.toString((System.nanoTime()-records.started)/1000000));
            records.history.publish(records.id,"ember-result-boot-id",Long.toString(currentBoot));
            records.history.publish(records.id,"ember-ground-packet-bytes","120");
            records.history.publish(records.id,"ember-capture-id",Long.toString(Integer.toUnsignedLong(b.getInt(34))));
            records.history.publish(records.id,"ember-record-count","5");
            records.history.publish(records.id,"ember-record-bytes","80");
            records.history.publish(records.id,"ember-records-sha256",digest);
            records.history.publish(records.id,"ember-sample-intervals-ms",intervals.toString());
            records.history.publish(records.id,"ember-retention-age-ms",Long.toString(Integer.toUnsignedLong(b.getInt(24)-b.getInt(104))));
            byte[] recordBytes=Arrays.copyOfRange(bytes,38,118);
            if(records.command==4){capturedBaseline=recordBytes;baselineBoot=currentBoot;baselineCapture=Integer.toUnsignedLong(b.getInt(34));}
            else {
                String match=capturedBaseline==null ? "NO_BASELINE" : Boolean.toString(baselineBoot==currentBoot &&
                    baselineCapture==Integer.toUnsignedLong(b.getInt(34)) && Arrays.equals(capturedBaseline,recordBytes));
                records.history.publish(records.id,"ember-records-match-capture",match);
                records.history.publish(records.id,"ember-ground-idle-ms",Long.toString(records.idleBeforeDispatchMs));
            }
            records.history.publishAck(records.id,"Acknowledge_EMBER_Acceptance",now,AckStatus.NA,"Correlated frozen record set received");
            records.history.publishAck(records.id,CommandHistoryPublisher.CommandComplete_KEY,now,AckStatus.OK);
            pending.remove(key(b));return;
        }
        if (Byte.toUnsignedInt(b.get(WireProfile.KIND)) == 1 &&
            Short.toUnsignedInt(b.getShort(WireProfile.MESSAGE_ID)) == 58) {
            Pending status = pending.get(key(b));
            if (status == null || (status.command != 2 && !(status.command==3 && status.parameter==1)) || bytes.length != 56 || b.get(30)!=1 ||
                Byte.toUnsignedInt(b.get(31))>4 || (b.get(32)!=1 && b.get(32)!=2) || b.get(53)!=0) return;
            long now=TimeEncoding.getWallclockTime();
            status.history.publish(status.id,"ember-outcome","COMPLETED");
            status.history.publish(status.id,"ember-elapsed-ms",Long.toString((System.nanoTime()-status.started)/1000000));
            status.history.publish(status.id,"ember-ground-packet-bytes",Integer.toString(bytes.length));
            status.history.publish(status.id,"ember-result-boot-id",Long.toString(currentBoot));
            String[] modes={"BOOT","STARTUP","COMMISSIONING","SAFE","NOMINAL"};
            status.history.publish(status.id,"ember-ihu-mode",modes[b.get(31)]);
            status.history.publish(status.id,"ember-ihu-outputs",Integer.toString(Byte.toUnsignedInt(b.get(33))));
            status.history.publish(status.id,"ember-boot-ready-ms",Long.toString(Integer.toUnsignedLong(b.getInt(34))));
            status.history.publish(status.id,"ember-can-ready",Integer.toString(Byte.toUnsignedInt(b.get(38))));
            status.history.publish(status.id,"ember-can-eflg",Integer.toString(Byte.toUnsignedInt(b.get(39))));
            status.history.publish(status.id,"ember-eps-valid",Integer.toString(Byte.toUnsignedInt(b.get(41))));
            status.history.publish(status.id,"ember-eps-age-ms",Long.toString(Integer.toUnsignedLong(b.getInt(42))));
            status.history.publish(status.id,"ember-health-gate-implemented","false");
            status.history.publishAck(status.id,"Acknowledge_EMBER_Acceptance",now,AckStatus.NA,"Correlated status snapshot received");
            status.history.publishAck(status.id,CommandHistoryPublisher.CommandComplete_KEY,now,AckStatus.OK);
            pending.remove(key(b));return;
        }
        if (Byte.toUnsignedInt(b.get(WireProfile.KIND)) == 1 &&
            Short.toUnsignedInt(b.getShort(WireProfile.MESSAGE_ID)) == 57) {
            Pending fire = pending.get(key(b));
            if (fire == null || fire.command != 1028 || bytes.length != 52 ||
                (b.get(30) != 1 && b.get(30) != 2) || (b.get(31) != 1 && b.get(31) != 2) ||
                Byte.toUnsignedInt(b.get(32)) > (b.get(30)==1 ? 1 : 2) ||
                (b.get(33) != 1 && b.get(33) != 2) || (b.get(32)==2 && b.get(33)!=2) ||
                b.getInt(38) == 0 || b.getInt(46) == 0) return;
            long now = TimeEncoding.getWallclockTime();
            String decision=b.get(32)==2 ? "UNKNOWN" : b.get(32)==0 ? "NO_FIRE" : "FIRE";
            fire.history.publish(fire.id, "ember-fire-result", decision);
            fire.history.publish(fire.id, "ember-analysis-result", decision);
            fire.history.publish(fire.id, "ember-fire-mode", b.get(33) == 1 ? "STATIC_STUB" : "ALGORITHM");
            fire.history.publish(fire.id, "ember-result-boot-id", Long.toString(currentBoot));
            fire.history.publish(fire.id, "ember-outcome", "COMPLETED");
            fire.history.publish(fire.id, "ember-elapsed-ms", Long.toString((System.nanoTime()-fire.started)/1000000));
            fire.history.publish(fire.id, "ember-application-result-bytes", "16");
            fire.history.publish(fire.id, "ember-ground-packet-bytes", Integer.toString(bytes.length));
            fire.history.publish(fire.id, "ember-payload-boot-id", Long.toString(Integer.toUnsignedLong(b.getInt(38))));
            fire.history.publish(fire.id, "ember-payload-check-id", Long.toString(Integer.toUnsignedLong(b.getInt(46))));
            if (!fire.accepted) fire.history.publishAck(fire.id, "Acknowledge_EMBER_Acceptance", now,
                AckStatus.NA, "Correlated payload final result received");
            fire.history.publishAck(fire.id, CommandHistoryPublisher.CommandComplete_KEY, now, AckStatus.OK);
            pending.remove(key(b));
            return;
        }
        if (Byte.toUnsignedInt(b.get(WireProfile.KIND)) != 2) return;
        Pending command = pending.get(key(b));
        if (command == null || Short.toUnsignedInt(b.getShort(WireProfile.COMMAND_RESPONSE_COMMAND_ID)) != command.command) return;
        int stage = Byte.toUnsignedInt(b.get(WireProfile.COMMAND_RESPONSE_STAGE));
        int reason = Short.toUnsignedInt(b.getShort(WireProfile.COMMAND_RESPONSE_REASON));
        String reasonName = WireProfile.reasonName(reason);
        if (stage > 3 || reasonName == null || ((stage == 0 || stage == 2) != (reason == 0))) return;
        long now = TimeEncoding.getWallclockTime();
        command.history.publish(command.id, "ember-result-boot-id", Long.toString(currentBoot));
        command.history.publish(command.id, "ember-result-reason", reason);
        command.history.publish(command.id, "ember-result-reason-name", reasonName);
        String reasonText = "reason " + reason + " (" + reasonName + ")";
        if (stage == 3 && command.command == 1028 && reason == 7) {
            long code = Integer.toUnsignedLong(b.getInt(WireProfile.COMMAND_RESPONSE_VALUE));
            String name = payloadErrorName(code);
            command.history.publish(command.id, "ember-payload-error-code", Long.toString(code));
            command.history.publish(command.id, "ember-payload-error-name", name);
            reasonText += ", payload error " + code + " (" + name + ")";
        }
        if(command.command==6 && stage==2){
            if(b.getInt(WireProfile.COMMAND_RESPONSE_VALUE)!=5000 || b.getShort(WireProfile.COMMAND_RESPONSE_PARAMETER_ID)!=0)return;
            command.history.publish(command.id,"ember-reboot-delay-ms","5000");
        }
        if (stage == 0) {
            if (!command.accepted) {
                command.accepted = true;
                command.deadline = System.nanoTime() + TimeUnit.SECONDS.toNanos(10);
                command.history.publishAck(command.id, "Acknowledge_EMBER_Acceptance", now, AckStatus.OK);
            }
            return;
        }
        if (stage == 2 && command.command == 0x30 &&
            (Short.toUnsignedInt(b.getShort(WireProfile.COMMAND_RESPONSE_PARAMETER_ID)) != command.parameter ||
             Integer.toUnsignedLong(b.getInt(WireProfile.COMMAND_RESPONSE_VALUE)) != command.value)) return;
        boolean singleByteSetting = command.command==SET_HEARTBEAT || command.command==SET_UHF_TELEMETRY ||
                                    command.command==SET_UHF_TELEMETRY_SET;
        if (stage==2 && (singleByteSetting || command.command==SET_UHF_TELEMETRY_SCHEDULE) &&
            ((singleByteSetting && command.value>1) ||
             b.getShort(WireProfile.COMMAND_RESPONSE_PARAMETER_ID)!=0 ||
             Integer.toUnsignedLong(b.getInt(WireProfile.COMMAND_RESPONSE_VALUE))!=command.value)) return;
        if (stage==2 && command.command==SET_UHF_TELEMETRY_SCHEDULE) {
            command.history.publish(command.id, "ember-listen-seconds", (int)(command.value>>>16));
            command.history.publish(command.id, "ember-telemetry-seconds", (int)(command.value&0xffff));
        }
        if (stage==2 && command.command==SET_UHF_TELEMETRY)
            command.history.publish(command.id, "ember-telemetry-enabled", (int)command.value);
        if (stage==2 && command.command==SET_UHF_TELEMETRY_SET)
            command.history.publish(command.id, "ember-telemetry-set", command.value==0 ? "BASIC" : "FULL");
        if (stage == 1 && command.accepted) return; // contradictory lifecycle
        if (stage == 1) command.history.publishAck(command.id, "Acknowledge_EMBER_Acceptance", now, AckStatus.NOK, "Rejected: " + reasonText);
        else if (!command.accepted) command.history.publishAck(command.id, "Acknowledge_EMBER_Acceptance", now,
                AckStatus.NA, "Acceptance report missing; correlated terminal result received");
        command.history.publish(command.id, "ember-outcome", stage == 2 ? "COMPLETED" : stage == 1 ? "REJECTED" : "EXECUTION_FAILED");
        command.history.publish(command.id, "ember-elapsed-ms", Long.toString((System.nanoTime()-command.started)/1000000));
        command.history.publish(command.id, "ember-ground-packet-bytes", Integer.toString(bytes.length));
        command.history.publishAck(command.id, CommandHistoryPublisher.CommandComplete_KEY, now,
                                  stage == 2 ? AckStatus.OK : AckStatus.NOK, "EMBER stage " + stage + ", " + reasonText);
        pending.remove(key(b));
    }
}
