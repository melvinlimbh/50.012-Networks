import config
import threading
import time
import udt
import util

"""
Selective Repeat

MAIN EVENTS
SENDER:
1. Data from above: Sender checks next available sequence number from upper layer 
of packets. If sequence number within the sender window, the data is packetized and sent;
otherwise return to the upper layer for later transmission.
2. Timeout: each packet has its own timer -> timeout -> resend -> reset timer
    2.1 keep trying until ACK received
3. ACK received: mark corresponding data packet as ACK'ed, stop packet timer
    3.1 if seqnum of packet = window base -> move window to next smallest unACK'ed packet

RECEIVER:
1. Packet with seqnum within range of receiving window [recv_base, recv_base+N-1]:
    1.1 send ACK to sender
    1.2 if not previously received: add to buffer
    1.3. if seqnum = receiving window base: deliver packets with next consecutive seqn
        to upper layer -> move base forward by number of packets delivered

2. if not within range of receiving window: ignore (i.e no ACKs -> wait for timeout)
3. Packet with seqnum in [recv_base-N, recv_base-1] received: packet already received,
send ACK 
-> (i think its to move sender window so that it will not keep sending this packet)
-> could be due to ACK message loss, and sender doesn't know the packet was ACK'ed
"""

class SelectiveRepeat:

  NO_PREV_ACK_MSG = "Don't have previous ACK to send, will wait for server to timeout."

  # "msg_handler" is used to deliver messages to application layer
  def __init__(self, local_port, remote_port, msg_handler):
    util.log("Starting up `Selective Repeat` protocol ... ")
    self.network_layer = udt.NetworkLayer(local_port, remote_port, self)
    self.msg_handler = msg_handler
    self.sender_base = 0
    self.next_sequence_number = 0
    self.receiver_last_ack = b''
    self.is_receiver = True
    self.sender_lock = threading.Lock()

    self.timer_ls = [self.set_timer(-1)]*config.WINDOW_SIZE
    self.sender_buffer = [b'']*config.WINDOW_SIZE
    self.ack_ls = [False]*config.WINDOW_SIZE

    self.receiver_base = 0
    self.recv_buffer = [b''] * config.WINDOW_SIZE
    self.recv_ack_ls = [False]*config.WINDOW_SIZE

  """
  timer is now for a packet with seqnum = seqnum
  => set_timer calls _timeout -> change set_timer and _timeout methods
  -> self.set_timer is no longer feasible, we need to keep track of packet timers
  -> can use list of window size since number of packets = window size
  -> self.set_timer() starts a Timer object
  """

  def set_timer(self,seqnum): 
    # threading.Timer(interval, function, args = None, kwargs = None)
    # args = empty list, kwargs = empty dictionary if no arguments given
    return threading.Timer((config.TIMEOUT_MSEC/1000.0), self._timeout,{seqnum:seqnum})

  def _timeout(self,seqnum): # timeout for 1 packet, find packet timer at tiemr_ls[index]
    util.log(f"Packet {seqnum} timeout")
    self.sender_lock.acquire()
    packet_index = (seqnum - self.sender_base) % config.WINDOW_SIZE
    # cancel, set and start timer -> i.e restart timer
    self.timer_ls[packet_index].cancel()
    self.timer_ls[packet_index] = self.set_timer(seqnum)
    packet = self.sender_buffer[packet_index]
    self.network_layer.send(packet)
    util.log("Resending packet: " + util.pkt_to_string(util.extract_data(packet)))
    self.timer_ls[packet_index].start()
    self.sender_lock.release()
    return

  """
  send method same, but change implementation of _send_helper method to include
  seqnum
  """
  def send(self, msg):
    self.is_receiver = False
    if self.next_sequence_number < (self.sender_base + config.WINDOW_SIZE):
      self._send_helper(msg)
      return True
    else:
      util.log("Window is full. App data rejected.")
      time.sleep(1)
      return False

  # Helper function for thread to send the next packet
  def _send_helper(self, msg):
    #print("=========TIMER LIST=======",self.timer_ls)
    self.sender_lock.acquire()
    packet = util.make_packet(msg, config.MSG_TYPE_DATA, self.next_sequence_number)
    packet_data = util.extract_data(packet)
    util.log("Sending data: " + util.pkt_to_string(packet_data))
    self.network_layer.send(packet) # send current packet

    if self.next_sequence_number < self.sender_base + config.WINDOW_SIZE:
      packet_index = (self.next_sequence_number - self.sender_base) % config.WINDOW_SIZE
      self.sender_buffer[packet_index] = packet
      self.ack_ls[packet_index] = False
      self.timer_ls[packet_index] = self.set_timer(self.next_sequence_number)
      self.timer_ls[packet_index].start()
      self.next_sequence_number += 1 # move to next seqnum

    else:
      pass
    self.sender_lock.release()
    return


  # "handler" to be called by network layer when packet is ready.
  def handle_arrival_msg(self):
    msg = self.network_layer.recv()
    msg_data = util.extract_data(msg)
    # NOTE: msg_data = Packet -> has seqnum

    # if sender: wait for timeout, if receiver: no ACK
    if(msg_data.is_corrupt): 
      util.log("Corrupted data, will wait for timeout")
      return 

    # not corrupt:
    """
    SENDER: 
    1. if corrupt: wait timeout, resend again, prob the scenario the 
    handout mentioned
    2. receives ACK
      2.1 update ack ls
      2.2 update timer ls
      2.3 move window base
      2.4 update buffer
    """
    if msg_data.msg_type == config.MSG_TYPE_ACK:
      self.sender_lock.acquire()
      packet_index = (msg_data.seq_num - self.sender_base) % config.WINDOW_SIZE
      self.ack_ls[packet_index] = True
      util.log(f"ACK received for packet {msg_data.seq_num}, cancelling timer.")
      self.timer_ls[packet_index].cancel() # restart
      self.timer_ls[packet_index] = self.set_timer(msg_data.seq_num)

      # for index,timer in enumerate(self.timer_ls):
      #   print(f"Timer alive for packet {index}: {timer.is_alive()}")
      # print(self.ack_ls)
      
      try: # move window base
        # find number of spots to move
      #   next_window_base = self.ack_ls.index(False)
      #   remaining_window = (config.WINDOW_SIZE - next_window_base) if next_window_base >= 1 else 0
      #   self.ack_ls = self.ack_ls[next_window_base:] + ([False]*remaining_window)
      #   self.timer_ls = self.timer_ls[next_window_base:] + ([self.set_timer(-1)]*remaining_window)
      #   self.sender_buffer = self.sender_buffer[next_window_base:] + [b''] * remaining_window
      #   self.sender_base += next_window_base
      # except ValueError: 
      #   pass
      
        while self.ack_ls[0] == True:
            self.sender_base += 1
            util.log(f"Updated send base to {self.sender_base}")
            self.ack_ls = self.ack_ls[1:] + [False]
            self.timer_ls = self.timer_ls[1:] + [
                self.set_timer(-1)
            ]
            self.sender_buffer = self.sender_buffer[1:] + [b'']
      except IndexError:
          pass
    
      self.sender_lock.release()
      

    # If DATA message, assume its for receiver
    """
    RECEIVER: if not in window: no ACK -> wait for timeout -> sender resend
    """
    if msg_data.msg_type == config.MSG_TYPE_DATA:
      util.log("Receiver received DATA: " + util.pkt_to_string(msg_data))
      ack_pkt = util.make_packet(b'', config.MSG_TYPE_ACK, msg_data.seq_num)

      receiving_window = [self.receiver_base, self.receiver_base+config.WINDOW_SIZE-1]
      if (msg_data.seq_num >= receiving_window[0] and 
                      msg_data.seq_num <= receiving_window[1]):

        self.network_layer.send(ack_pkt)
        util.log(f"ACK sent for packet {msg_data.seq_num}")
        self.receiver_last_ack = ack_pkt
        packet_index = (msg_data.seq_num - self.receiver_base) % config.WINDOW_SIZE
        self.recv_ack_ls[packet_index] = True

        if msg_data.seq_num != self.receiver_base:
          self.recv_buffer[packet_index] = msg_data.payload

        else:
          self.recv_buffer[packet_index] = msg_data.payload
          try: 
            while self.recv_ack_ls[0] == True:
              self.msg_handler(self.recv_buffer[0])
              self.receiver_base += 1
              self.recv_ack_ls = self.recv_ack_ls[1:] + [False]
              self.recv_buffer = self.recv_buffer[1:] + [b'']
              util.log(
                  f"Updated receiver base to {self.receiver_base}")
          except IndexError: pass

      elif msg_data.seq_num < self.receiver_base:
                self.network_layer.send(ack_pkt)
                util.log("Packet outside receiver window")
                util.log("Sent ACK: " + util.pkt_to_string(util.extract_data(ack_pkt)))
      
      else: return
    return

  # Cleanup resources and cancel all timers
  def shutdown(self):
    if not self.is_receiver: self._wait_for_last_ACK() # sender
    for _ in self.timer_ls: # iterate timer ls for Timer objects
        if _.is_alive(): _.cancel()
    util.log("Connection shutting down...")
    self.network_layer.shutdown()


  def _wait_for_last_ACK(self):
    while self.sender_base < self.next_sequence_number-1:
      util.log("Waiting for last ACK from receiver with sequence # "
                + str(int(self.next_sequence_number-1)) + ".")
      time.sleep(1)
