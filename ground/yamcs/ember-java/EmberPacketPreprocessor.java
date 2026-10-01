package com.example.ember;

import java.nio.ByteBuffer;
import java.util.HashMap;
import java.util.Map;
import org.yamcs.TmPacket;
import org.yamcs.YConfiguration;
import org.yamcs.tctm.AbstractPacketPreprocessor;
import org.yamcs.utils.TimeEncoding;

/** Reject malformed packets before archive/XTCE. Uptime is not UTC. */
public class EmberPacketPreprocessor extends AbstractPacketPreprocessor {
    private final Map<String, Integer> previous = new HashMap<>();
    private final EmberResults results;
    public EmberPacketPreprocessor(String instance) { this(instance, YConfiguration.emptyConfig()); }
    public EmberPacketPreprocessor(String instance, YConfiguration config) {
        super(instance, config);
        results = EmberResults.forInstance(instance);
    }

    private TmPacket discard(String reason) {
        eventProducer.sendWarning("EMBER_INVALID_PACKET", reason);
        return null;
    }

    @Override public TmPacket process(TmPacket packet) {
        byte[] bytes = packet.getPacket();
        if (bytes.length < WireProfile.PAYLOAD + 2 || bytes.length > WireProfile.MAX_PACKET) {
            return discard("Packet size outside profile");
        }
        ByteBuffer b = ByteBuffer.wrap(bytes);
        int identity = Short.toUnsignedInt(b.getShort(0));
        int seq = Short.toUnsignedInt(b.getShort(2));
        int kind = Byte.toUnsignedInt(b.get(WireProfile.KIND));
        int message = Short.toUnsignedInt(b.getShort(WireProfile.MESSAGE_ID));
        int payload = WireProfile.payloadLength(kind, message);
        int source = Byte.toUnsignedInt(b.get(WireProfile.SOURCE));
        int target = Byte.toUnsignedInt(b.get(WireProfile.TARGET));
        long epoch = Integer.toUnsignedLong(b.getInt(WireProfile.TRANSACTION_EPOCH));
        long transaction = Integer.toUnsignedLong(b.getInt(WireProfile.TRANSACTION_ID));
        long boot = Integer.toUnsignedLong(b.getInt(WireProfile.SOURCE_BOOT_ID));
        if (identity != WireProfile.DOWNLINK_IDENTITY || seq >>> 14 != 3 ||
            Short.toUnsignedInt(b.getShort(4)) + 7 != bytes.length ||
            Byte.toUnsignedInt(b.get(WireProfile.SCHEMA_VERSION)) != WireProfile.SCHEMA ||
            payload < 0 || payload != Short.toUnsignedInt(b.getShort(WireProfile.PAYLOAD_LENGTH)) ||
            WireProfile.PAYLOAD + payload + 2 != bytes.length ||
            source < 2 || source > 4 || target != 1 || boot == 0 ||
            (epoch == 0) != (transaction == 0) ||
            (kind == 2 && (source != 2 || transaction == 0))) {
            return discard("Header, identity or payload mismatch");
        }
        if (WireChecks.crc(bytes, bytes.length - 2) != Short.toUnsignedInt(b.getShort(bytes.length - 2))) {
            return discard("CRC mismatch");
        }
        // Bound tracking to one active boot per source (three allowed sources).
        String key = Integer.toString(source);
        int count = seq & 0x3fff;
        String bootKey = key + "-boot";
        if (previous.getOrDefault(bootKey, (int) boot) != (int) boot) previous.remove(key);
        Integer old = previous.put(key, count);
        previous.put(bootKey, (int) boot);
        if (old != null && ((count - old) & 0x3fff) != 1) {
            eventProducer.sendWarning("EMBER_SEQUENCE_GAP", "Source " + source + " previous " + old + " current " + count);
        }
        // Archive generationTime is ground reception time, not spacecraft UTC.
        packet.setGenerationTime(TimeEncoding.getWallclockTime());
        packet.setSequenceCount(b.getInt(0));
        results.observe(bytes);
        return packet;
    }
}
