package com.example.ember;

import java.util.Arrays;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

/** Bounded, per-instance exact-byte duplicate filter shared by all TM links.
 * No fuzzy sequence matching: boot, uptime, provenance and payload all matter.
 * This only suppresses recent live arrivals; restart/replay is a new session. */
public final class EmberDuplicates {
    private static final Map<String, EmberDuplicates> INSTANCES = new ConcurrentHashMap<>();
    private final Map<Key, Long> seen = new LinkedHashMap<>();
    private static final long TTL = 120_000_000_000L;
    private static final int CAPACITY = 4096;
    private static final class Key {
        final byte[] bytes;
        Key(byte[] bytes) { this.bytes = bytes.clone(); }
        @Override public int hashCode() { return Arrays.hashCode(bytes); }
        @Override public boolean equals(Object other) {
            return other instanceof Key && Arrays.equals(bytes, ((Key) other).bytes);
        }
    }
    public static EmberDuplicates forInstance(String name) {
        return INSTANCES.computeIfAbsent(name, ignored -> new EmberDuplicates());
    }
    public synchronized boolean first(byte[] bytes, long now) {
        var it = seen.entrySet().iterator();
        while (it.hasNext()) {
            var entry = it.next();
            if (now - entry.getValue() < TTL) break;
            it.remove();
        }
        Key key = new Key(bytes);
        if (seen.containsKey(key)) return false;
        if (seen.size() >= CAPACITY) seen.remove(seen.keySet().iterator().next());
        seen.put(key, now);
        return true;
    }
}
