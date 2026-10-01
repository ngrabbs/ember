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
        command.deadline = System.nanoTime() + TimeUnit.SECONDS.toNanos(5);
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
    public synchronized void observe(byte[] bytes) {
        ByteBuffer b = ByteBuffer.wrap(bytes);
        int source = Byte.toUnsignedInt(b.get(WireProfile.SOURCE));
        if (source != 2) return;
        long currentBoot = Integer.toUnsignedLong(b.getInt(WireProfile.SOURCE_BOOT_ID));
        if (boot != 0 && boot != currentBoot) {
            pending.values().forEach(command -> unknown(command, "Unknown outcome: IHU boot identity changed"));
            pending.clear();
        }
        boot = currentBoot;
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
