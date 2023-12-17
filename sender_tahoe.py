import socket
import time

# total packet size
PACKET_SIZE = 1024
# bytes reserved for sequence id
SEQ_ID_SIZE = 4
# bytes available for message
MESSAGE_SIZE = PACKET_SIZE - SEQ_ID_SIZE
# total packets to send
WINDOW_SIZE = 1
THRESHOLD = 64

# read data
with open('/Users/evant/Documents/ECS 152A/congestion_control_ecs152a-main/docker/file.mp3', 'rb') as f:
    data = f.read()
 
# create a udp socket
with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:
    start_time = time.time()

    # bind the socket to a OS port
    udp_socket.bind(("localhost", 5000))
    udp_socket.settimeout(1)
    
    # start sending data from 0th sequence
    seq_id = 0
    timers = {}
    while seq_id < len(data):
        # create messages
        messages = []
        acks = {}

        for i in range(WINDOW_SIZE):
            if seq_id < len(data):
                message = int.to_bytes(seq_id, SEQ_ID_SIZE, byteorder='big', signed=True) + data[seq_id : seq_id + MESSAGE_SIZE]
                messages.append((seq_id, message))
                acks[seq_id] = False
                timers[seq_id] = time.time()
                seq_id += MESSAGE_SIZE

        # send messages
        for _, message in messages:
            udp_socket.sendto(message, ('localhost', 5001))
        
        WINDOW_MOD = False
        # wait for acknowledgement
        while True:
            try:
                # wait for ack
                ack, _ = udp_socket.recvfrom(PACKET_SIZE)
                end_delay = time.time()
                
                # extract ack id
                ack_id = int.from_bytes(ack[:SEQ_ID_SIZE], byteorder='big')

                if ack_id == len(data):
                    acks[len(data) - (len(data) % MESSAGE_SIZE)] = True
                else:
                    acks[ack_id - MESSAGE_SIZE] = True

                if ack_id - MESSAGE_SIZE in timers:
                    timers[ack_id - MESSAGE_SIZE] = end_delay - timers[ack_id - MESSAGE_SIZE]
                    if timers[ack_id - MESSAGE_SIZE] > 1:
                        WINDOW_MOD = True
                        THRESHOLD = WINDOW_SIZE / 2
                        WINDOW_SIZE = 1

                # all acks received, move on
                if all(acks.values()):
                    if not WINDOW_MOD:
                        if WINDOW_SIZE >= THRESHOLD:
                            WINDOW_SIZE += 1
                        else:
                            WINDOW_SIZE *= 2
                    break
            except socket.timeout:
                # no ack received, resend unacked messages
                for sid, message in messages:
                    if not acks[sid]:
                        udp_socket.sendto(message, ('localhost', 5001))
                        
                        # Update timer only for unacknowledged packets
                        timers[sid] = time.time()

    final_message = int.to_bytes(len(data), SEQ_ID_SIZE, signed=True, byteorder='big') + b''
    udp_socket.sendto(final_message, ('localhost', 5001))

    while True:
        try:
            ack, _ = udp_socket.recvfrom(PACKET_SIZE)
            ack_id = int.from_bytes(ack[:SEQ_ID_SIZE], byteorder='big')

            if ack_id == len(data) + 3:
                end_time = time.time()
                break
        except socket.timeout:
            udp_socket.sendto(final_message, ('localhost', 5001))

    finack_message = int.to_bytes(seq_id + 1, SEQ_ID_SIZE, signed=True, byteorder='big') + b'==FINACK=='
    udp_socket.sendto(finack_message, ('localhost', 5001))

    time_elapsed = end_time - start_time
    throughput = len(data) / time_elapsed
    timers.popitem()
    per_packet_delay = sum(timers.values()) / len(timers.values())
    performance_metric = throughput / per_packet_delay

    print(f"{round(throughput, 2)}, {round(per_packet_delay, 2)}, {round(performance_metric, 2)}")