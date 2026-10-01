package com.example.ember;

import java.nio.ByteBuffer;
import java.security.SecureRandom;
import org.yamcs.YConfiguration;
import org.yamcs.cmdhistory.CommandHistoryPublisher;
import org.yamcs.commanding.PreparedCommand;
import org.yamcs.tctm.CommandPostprocessor;
import org.yamcs.tctm.Link;

/** Allocate bench transaction identity after XTCE argument encoding. */
public class EmberCommandPostprocessor implements CommandPostprocessor {
    private final SecureRandom random = new SecureRandom();
    private int epoch = newEpoch();
    private long transaction = 0;
    private int sequence = 0;
    private final long start = System.nanoTime();
    private CommandHistoryPublisher history;
    private EmberResults results;

    private int newEpoch() { return random.nextInt(Integer.MAX_VALUE) + 1; }
    @Override public void init(String instance, YConfiguration config, Link link) { results = EmberResults.forInstance(instance); }
    @Override public void setCommandHistoryPublisher(CommandHistoryPublisher publisher) { history = publisher; }

    @Override public synchronized byte[] process(PreparedCommand command) {
        byte[] bytes = command.getBinary();
        if (bytes.length < WireProfile.PAYLOAD + 2 || bytes.length > WireProfile.MAX_PACKET) {
            throw new IllegalArgumentException("EMBER command size outside bench profile");
        }
        if (transaction == 0xffffffffL) {
            epoch = newEpoch();
            transaction = 0;
        }
        transaction++;
        ByteBuffer buffer = ByteBuffer.wrap(bytes);
        buffer.putShort(2, (short) (0xc000 | sequence));
        sequence = (sequence + 1) & 0x3fff;
        buffer.putShort(4, (short) (bytes.length - 7));
        buffer.putInt(WireProfile.TRANSACTION_EPOCH, epoch);
        buffer.putInt(WireProfile.TRANSACTION_ID, (int) transaction);
        buffer.putInt(WireProfile.SOURCE_BOOT_ID, epoch);
        buffer.putInt(WireProfile.UPTIME_MS, (int) ((System.nanoTime() - start) / 1000000));
        buffer.putShort(bytes.length - 2, (short) WireChecks.crc(bytes, bytes.length - 2));
        history.publish(command.getCommandId(), "ember-transaction-epoch", Integer.toString(epoch));
        history.publish(command.getCommandId(), "ember-transaction-id", Long.toString(transaction));
        history.publish(command.getCommandId(), PreparedCommand.CNAME_BINARY, bytes);
        results.register(command.getCommandId(), history, bytes);
        return bytes;
    }
}
