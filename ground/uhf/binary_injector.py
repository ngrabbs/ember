"""Opaque packet admission, bounded queue and native GNU Radio pipe injection."""
from collections import OrderedDict,deque
import hashlib,json,os,queue,select,threading,time
from packet_radio import waveform

class PacketQueue:
    def __init__(self, prepare=None, max_age=15, clock=time.monotonic, event=None):
        self.prepare=prepare or (lambda payload,seq:waveform(payload,seq).tobytes())
        self.clock=clock;self.max_age=max_age;self.event=event or (lambda **record:None)
        self.pending=queue.Queue(maxsize=2);self.cache=OrderedDict();self.sequence=0
        self.accepting=True;self.expired=0;self.rejected=0;self.lock=threading.RLock()
    def enqueue(self, hexdata, request_id):
        with self.lock:
            if not self.accepting:raise ValueError('Flow is stopping')
            if not isinstance(request_id,str) or not 1<=len(request_id)<=64:raise ValueError('Request ID must be 1..64 characters')
            if not isinstance(hexdata,str) or len(hexdata)>480:raise ValueError('Binary hex required')
            payload=bytes.fromhex(hexdata)
            if not 1<=len(payload)<=240:raise ValueError('Payload must be 1..240 bytes')
            digest=hashlib.sha256(payload).hexdigest()
            if request_id in self.cache:
                original,result=self.cache[request_id]
                if original!=digest:raise ValueError('Request ID conflicts with previous payload')
                return dict(result,duplicate_request=True)
            if self.pending.full():self.rejected+=1;raise ValueError('Packet queue full')
            seq=self.sequence+1
            if seq>0xffffffff:raise ValueError('Sequence exhausted')
            start=self.clock();data=self.prepare(payload,seq)
            if not self.accepting:raise ValueError('Flow is stopping')
            result=dict(sequence=seq,request_id=request_id,sha256=digest,hex=payload.hex(),
                samples=len(data)//8,preparation_seconds=self.clock()-start,state='queued',
                note='Admission is not RF delivery')
            self.pending.put_nowait((data,result,self.clock()));self.sequence=seq
            self.cache[request_id]=(digest,result)
            if len(self.cache)>64:self.cache.popitem(last=False)
            self.event(event='QUEUED',**result)
            return result
    def take(self):
        while True:
            try:data,meta,at=self.pending.get_nowait()
            except queue.Empty:return None
            self.pending.task_done()
            if self.clock()-at>self.max_age:
                self.expired+=1;self.event(event='EXPIRED',sequence=meta['sequence']);continue
            return data,meta

class StreamInjector:
    def __init__(self, event=None, prepare=None, max_age=15):
        from gnuradio import gr,blocks
        self.queue=PacketQueue(prepare=prepare,max_age=max_age,event=event)
        self.event=self.queue.event;self.stop_event=threading.Event();self.error=None
        self.reader,self.writer=os.pipe();os.set_blocking(self.writer,False)
        self.source=blocks.file_descriptor_source(gr.sizeof_gr_complex,self.reader,False)
        self.records=deque(maxlen=64);self.records_lock=threading.Lock();self.emitted=0
        self.thread=threading.Thread(target=self.feed,daemon=True);self.thread.start()
    def feed(self):
        written=0;zeros=bytes(65536*8)
        try:
            while not self.stop_event.is_set():
                item=self.queue.take()
                if item is None:data=zeros
                else:
                    data,meta=item
                    with self.records_lock:self.records.append(dict(sequence=meta['sequence'],begin=written,end=written+len(data)//8,emitted=False))
                view=memoryview(data);at=0
                while at<len(view) and not self.stop_event.is_set():
                    try:at+=os.write(self.writer,view[at:])
                    except BlockingIOError:select.select([],[self.writer],[],.1)
                written+=at//8
        except Exception as exc:self.error=str(exc);self.queue.accepting=False
        finally:os.close(self.writer)
    def status(self, consumed):
        with self.records_lock:
            for r in self.records:
                if consumed>=r['end'] and not r['emitted']:
                    r['emitted']=True;self.emitted+=1;self.event(event='SAMPLES_PASSED_DOWNSTREAM',sequence=r['sequence'])
            records=list(self.records)
        return dict(accepted=self.queue.sequence,queued=self.queue.pending.qsize(),expired=self.queue.expired,
            queue_full=self.queue.rejected,emitted=self.emitted,output_samples=int(consumed),writer_error=self.error,
            accepting=self.queue.accepting,recent_packets=records[-12:],note='Downstream samples are not RF reception')
    def close(self):
        self.queue.accepting=False;self.stop_event.set();self.thread.join(timeout=3)
        if self.thread.is_alive():raise RuntimeError('Pipe writer failed to stop')
