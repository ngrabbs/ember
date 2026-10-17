import com.example.ember.EmberDuplicates;
import java.nio.ByteBuffer;

public class EmberDuplicatesTest {
    public static void main(String[] args) {
        var a = EmberDuplicates.forInstance("ttl-check");
        byte[] packet = {1,2,3};
        if (!a.first(packet,0) || a.first(packet,1)) throw new AssertionError("duplicate");
        packet[0]=9;
        if (!a.first(packet,2)) throw new AssertionError("different payload");
        if (!a.first(new byte[]{1,2,3},120_000_000_000L)) throw new AssertionError("expiry");
        if (!EmberDuplicates.forInstance("another-instance").first(packet,3)) throw new AssertionError("instance isolation");
        var b = EmberDuplicates.forInstance("capacity-check");
        for (int i=0;i<4097;i++) if (!b.first(ByteBuffer.allocate(4).putInt(i).array(),i)) throw new AssertionError("unique");
        if (!b.first(new byte[4],5000)) throw new AssertionError("bounded eviction");
        System.out.println("Exact bytes, expiry, instance isolation and bounded eviction PASS");
    }
}
