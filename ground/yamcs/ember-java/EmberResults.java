package com.example.ember;

import java.nio.ByteBuffer;
import java.util.HashMap;
import java.util.Map;
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
    private static final class Pending {
        CommandId id;
        CommandHistoryPublisher history;
        int command, parameter;
        long value, deadline;
        boolean accepted;
    }
    private final Map<String, Pending> pending = new HashMap<>();
    private long boot;

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
        if (command.command == 1024) {
            command.parameter = Short.toUnsignedInt(b.getShort(WireProfile.PAYLOAD_PING_BYTES));
        }
        boolean payloadCommand = command.command >= 1024 && command.command <= 1028;
        int resultTimeoutSeconds = 5;
        if (command.command == 1) {
            resultTimeoutSeconds = 10;
        } else if (payloadCommand || (command.command >= 11 && command.command <= 14)) {
            resultTimeoutSeconds = 40;
        }
        command.deadline = System.nanoTime() + TimeUnit.SECONDS.toNanos(resultTimeoutSeconds);
        pending.put(key(b), command);
        history.publishAck(id, "Acknowledge_EMBER_Acceptance", TimeEncoding.getWallclockTime(), AckStatus.PENDING);
        history.publishAck(id, CommandHistoryPublisher.CommandComplete_KEY, TimeEncoding.getWallclockTime(), AckStatus.PENDING);
    }
    private void unknown(Pending command, String reason) {
        long now = TimeEncoding.getWallclockTime();
        if (!command.accepted) command.history.publishAck(command.id, "Acknowledge_EMBER_Acceptance", now, AckStatus.TIMEOUT, reason);
        command.history.publish(command.id, "ember-outcome", "UNKNOWN");
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
    private boolean payloadQueryMatches(Pending command, ByteBuffer b, int message) {
        if (command == null) return false;
        switch (command.command) {
            case 1024: return message == 56 &&
                b.get(WireProfile.PAYLOAD_PING_RESULT_TRANSPORT) == 2 &&
                b.getInt(WireProfile.PAYLOAD_PING_RESULT_REPORTED_BOOT_ID) != 0 &&
                b.get(WireProfile.PAYLOAD_PING_RESULT_ECHO_OK) == 1 &&
                Short.toUnsignedInt(b.getShort(WireProfile.PAYLOAD_PING_RESULT_BYTES)) == command.parameter;
            case 1025: return message == 55 &&
                b.get(WireProfile.PAYLOAD_FIRMWARE_TRANSPORT) == 2 &&
                b.getInt(WireProfile.PAYLOAD_FIRMWARE_REPORTED_BOOT_ID) != 0 &&
                Byte.toUnsignedInt(b.get(WireProfile.PAYLOAD_FIRMWARE_DIRTY)) <= 1;
            case 1026:
            case 1027: return message == 54 &&
                b.get(WireProfile.PAYLOAD_STATUS_TRANSPORT) == 2 &&
                b.get(WireProfile.PAYLOAD_STATUS_PAYLOAD_VERSION) == 1 &&
                b.get(WireProfile.PAYLOAD_STATUS_NODE) == 4 &&
                b.get(WireProfile.PAYLOAD_STATUS_READY) == 1 &&
                b.getInt(WireProfile.PAYLOAD_STATUS_REPORTED_BOOT_ID) != 0 &&
                b.get(WireProfile.PAYLOAD_STATUS_REPORT_KIND) == (command.command == 1026 ? 1 : 2);
            default: return false;
        }
    }

    private void completePayload(Pending command, String key, long sourceBoot) {
        long now = TimeEncoding.getWallclockTime();
        command.history.publish(command.id, "ember-result-boot-id", Long.toString(sourceBoot));
        command.history.publish(command.id, "ember-outcome", "COMPLETED");
        if (!command.accepted) command.history.publishAck(command.id, "Acknowledge_EMBER_Acceptance", now,
            AckStatus.NA, "Correlated payload result received");
        command.history.publishAck(command.id, CommandHistoryPublisher.CommandComplete_KEY, now, AckStatus.OK);
        pending.remove(key);
    }

    public synchronized void observe(byte[] bytes) {
        ByteBuffer b = ByteBuffer.wrap(bytes);
        int source = Byte.toUnsignedInt(b.get(WireProfile.SOURCE));
        if (source != 2) return;
        // A host-wrapped EPS observation uses the bridge's session as its boot.
        // It is telemetry provenance, never evidence that the physical IHU reset.
        if (Short.toUnsignedInt(b.getShort(WireProfile.MESSAGE_ID)) == 0x10 &&
            Byte.toUnsignedInt(b.get(WireProfile.POWER_STATUS_PROVENANCE)) != 2) return;
        boolean faultSnapshot = Byte.toUnsignedInt(b.get(WireProfile.KIND)) == 1 &&
            Short.toUnsignedInt(b.getShort(WireProfile.MESSAGE_ID)) == 64 &&
            b.get(WireProfile.IHU_FAULTS_PAYLOAD_VERSION) == 1 &&
            Byte.toUnsignedInt(b.get(WireProfile.IHU_FAULTS_COUNT)) ==
                Math.min(Integer.toUnsignedLong(b.getInt(WireProfile.IHU_FAULTS_TOTAL)), 16);
        boolean radioConfig = Byte.toUnsignedInt(b.get(WireProfile.KIND)) == 1 &&
            Short.toUnsignedInt(b.getShort(WireProfile.MESSAGE_ID)) == 65 &&
            b.get(WireProfile.RADIO_CONFIG_SCHEMA_VERSION) == 2 &&
            b.getInt(WireProfile.RADIO_CONFIG_RADIO_BOOT_ID) != 0;
        long currentBoot = Integer.toUnsignedLong(b.getInt(WireProfile.SOURCE_BOOT_ID));
        if (boot != 0 && boot != currentBoot) {
            String responseKey = key(b);
            pending.entrySet().removeIf(entry -> {
                Pending command = entry.getValue();
                if (entry.getKey().equals(responseKey) &&
                    ((faultSnapshot && command.command == 11) || (radioConfig && command.command >= 12 && command.command <= 14))) return false;
                unknown(command, "Unknown outcome: IHU boot identity changed");
                return true;
            });
        }
        boot = currentBoot;
        if (b.get(WireProfile.KIND) == 1) {
            String responseKey = key(b);
            Pending query = pending.get(responseKey);
            if (payloadQueryMatches(query, b, Short.toUnsignedInt(b.getShort(WireProfile.MESSAGE_ID)))) {
                completePayload(query, responseKey, currentBoot);
                return;
            }
        }
        int message = Short.toUnsignedInt(b.getShort(WireProfile.MESSAGE_ID));
        if (b.get(WireProfile.KIND) == 1 && (message == 57 || message == 61)) {
            String responseKey = key(b);
            Pending fire = pending.get(responseKey);
            int version = Byte.toUnsignedInt(b.get(WireProfile.PAYLOAD_FIRE_RESULT_PAYLOAD_VERSION));
            int result = Byte.toUnsignedInt(b.get(WireProfile.PAYLOAD_FIRE_RESULT_RESULT));
            int mode = Byte.toUnsignedInt(b.get(WireProfile.PAYLOAD_FIRE_RESULT_EXECUTION_MODE));
            int transport = Byte.toUnsignedInt(b.get(WireProfile.PAYLOAD_FIRE_RESULT_TRANSPORT));
            if (fire == null || fire.command != 1028 || (version != 1 && version != 2) ||
                (transport != 1 && transport != 2) || result > (version == 1 ? 1 : 2) ||
                (mode != 1 && mode != 2) || (result == 2 && mode != 2) ||
                b.getInt(WireProfile.PAYLOAD_FIRE_RESULT_REPORTED_BOOT_ID) == 0 ||
                b.getInt(WireProfile.PAYLOAD_FIRE_RESULT_CHECK_ID) == 0) return;
            fire.history.publish(fire.id, "ember-fire-result",
                result == 0 ? "NO_FIRE" : result == 1 ? "FIRE" : "UNKNOWN");
            fire.history.publish(fire.id, "ember-fire-mode", mode == 1 ? "STATIC_STUB" : "ALGORITHM");
            completePayload(fire, responseKey, currentBoot);
            return;
        }
        if (radioConfig) {
            Pending config = pending.get(key(b));
            if (config == null || config.command < 12 || config.command > 14) return;
            int result = Byte.toUnsignedInt(b.get(WireProfile.RADIO_CONFIG_OPERATION_RESULT));
            int expected = config.command == 12 ? 0 : config.command == 13 ? 1 : 3;
            boolean rejected = config.command != 12 && result == 2;
            if (result != expected && !rejected) return;
            long now = TimeEncoding.getWallclockTime();
            config.history.publish(config.id, "ember-result-boot-id", Long.toString(currentBoot));
            config.history.publish(config.id, "ember-radio-boot-id",
                Integer.toUnsignedString(b.getInt(WireProfile.RADIO_CONFIG_RADIO_BOOT_ID)));
            config.history.publish(config.id, "ember-radio-trial-state",
                Byte.toUnsignedInt(b.get(WireProfile.RADIO_CONFIG_TRIAL_STATE)));
            config.history.publish(config.id, "ember-outcome", rejected ? "REJECTED" : "COMPLETED");
            config.history.publishAck(config.id, "Acknowledge_EMBER_Acceptance", now,
                rejected ? AckStatus.NOK : AckStatus.NA, "Correlated transceiver configuration received");
            config.history.publishAck(config.id, CommandHistoryPublisher.CommandComplete_KEY, now,
                rejected ? AckStatus.NOK : AckStatus.OK);
            pending.remove(key(b));
            return;
        }
        if (faultSnapshot) {
            Pending faults = pending.get(key(b));
            if (faults == null || faults.command != 11) return;
            int count = Byte.toUnsignedInt(b.get(WireProfile.IHU_FAULTS_COUNT));
            long now = TimeEncoding.getWallclockTime();
            faults.history.publish(faults.id, "ember-result-boot-id", Long.toString(currentBoot));
            faults.history.publish(faults.id, "ember-retained-faults", count);
            faults.history.publish(faults.id, "ember-outcome", "COMPLETED");
            if (!faults.accepted) faults.history.publishAck(faults.id, "Acknowledge_EMBER_Acceptance", now,
                AckStatus.NA, "Correlated IHU fault history received");
            faults.history.publishAck(faults.id, CommandHistoryPublisher.CommandComplete_KEY, now, AckStatus.OK);
            pending.remove(key(b));
            return;
        }
        if (Byte.toUnsignedInt(b.get(WireProfile.KIND)) != 2) return;
        Pending command = pending.get(key(b));
        if (command == null || Short.toUnsignedInt(b.getShort(WireProfile.COMMAND_RESPONSE_COMMAND_ID)) != command.command) return;
        int stage = Byte.toUnsignedInt(b.get(WireProfile.COMMAND_RESPONSE_STAGE));
        int reason = Short.toUnsignedInt(b.getShort(WireProfile.COMMAND_RESPONSE_REASON));
        if (stage > 3 || reason > 9 || ((stage == 0 || stage == 2) != (reason == 0))) return;
        long now = TimeEncoding.getWallclockTime();
        command.history.publish(command.id, "ember-result-boot-id", Long.toString(currentBoot));
        command.history.publish(command.id, "ember-result-reason", reason);
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
        if (stage == 1 && command.accepted) return; // contradictory lifecycle
        if (stage == 1) command.history.publishAck(command.id, "Acknowledge_EMBER_Acceptance", now, AckStatus.NOK, "Rejected: reason " + reason);
        else if (!command.accepted) command.history.publishAck(command.id, "Acknowledge_EMBER_Acceptance", now,
                AckStatus.NA, "Acceptance report missing; correlated terminal result received");
        command.history.publish(command.id, "ember-outcome", stage == 2 ? "COMPLETED" : stage == 1 ? "REJECTED" : "EXECUTION_FAILED");
        command.history.publishAck(command.id, CommandHistoryPublisher.CommandComplete_KEY, now,
                                  stage == 2 ? AckStatus.OK : AckStatus.NOK, "EMBER stage " + stage + ", reason " + reason);
        pending.remove(key(b));
    }
}
