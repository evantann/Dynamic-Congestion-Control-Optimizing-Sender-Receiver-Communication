import socket
import time

PACKET_SIZE = 1024
SEQ_ID_SIZE = 4
MESSAGE_SIZE = PACKET_SIZE - SEQ_ID_SIZE
WINDOW_SIZE = 100

with open('/Users/evant/Documents/ECS 152A/congestion_control_ecs152a-main/docker/file.mp3', 'rb') as f:
    data = f.read()

with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:
    start_time = time.time()

    udp_socket.bind(("localhost", 5000))
    udp_socket.settimeout(1)

    seq_id = 0
    messages = []
    acks = {}
    timers = {}

    for i in range(WINDOW_SIZE):
        if seq_id + MESSAGE_SIZE < len(data):
            message = int.to_bytes(seq_id, SEQ_ID_SIZE, byteorder='big', signed=True) + data[seq_id: seq_id + MESSAGE_SIZE]
            messages.append((seq_id, message))
            udp_socket.sendto(message, ('localhost', 5001))
            acks[seq_id] = False
            timers[seq_id] = time.time()
            seq_id += MESSAGE_SIZE

    left = MESSAGE_SIZE
    window_ack = 0

    while True:
        try:
            ack, _ = udp_socket.recvfrom(PACKET_SIZE)
            ack_id = int.from_bytes(ack[:SEQ_ID_SIZE], byteorder='big')
            end_delay = time.time()

            if ack_id - MESSAGE_SIZE in timers:
                timers[ack_id - MESSAGE_SIZE] = end_delay - timers[ack_id - MESSAGE_SIZE]

            if ack_id == len(data):
                acks[len(data) - (len(data) % MESSAGE_SIZE)] = True
            else:
                acks[ack_id - MESSAGE_SIZE] = True

            if all(acks.values()):
                break

            window_ack += 1

            if seq_id + MESSAGE_SIZE < len(data) and acks[left]:
                while window_ack > 0:
                    message = int.to_bytes(seq_id, SEQ_ID_SIZE, byteorder='big', signed=True) + data[seq_id: seq_id + MESSAGE_SIZE]
                    messages.append((seq_id, message))
                    acks[seq_id] = False
                    timers[seq_id] = time.time()
                    udp_socket.sendto(message, ('localhost', 5001))
                    if seq_id + MESSAGE_SIZE < len(data):
                        seq_id += MESSAGE_SIZE
                    left += MESSAGE_SIZE
                    window_ack -= 1

        except socket.timeout:
            for sid, message in messages:
                if not acks[sid]:
                    udp_socket.sendto(message, ('localhost', 5001))
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