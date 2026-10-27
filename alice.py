import socket
import json
import threading
import sys
from aes import cipher_aes_custom, encrypt_with_nonce

CONFIG_PATH = "keys.json"

def get_ka():
    try:
        with open(CONFIG_PATH, "r") as f: return json.load(f).get("NodeA", "MasterKeyForA_12").encode('utf-8')
    except:
        return b"MasterKeyForA_12"

def receive_chat(sock, ks):
    while True:
        try:
            data = sock.recv(1024)
            if not data:
                print("\n[Sistem] Koneksi terputus dari Node B.")
                break
            
            #log
            print(f"\nrecv: [{data.hex()}]")
            #============= CIPHER
            dec_msg = cipher_aes_custom(ks, data[8:], nonce=data[:8])[8:].decode('utf-8')
            print(f"[Node B] : {dec_msg}")
            print("[Node A] : ", end="")
            sys.stdout.flush()
        except Exception as e:
            break

def run_handshake():
    ka = get_ka()
    print(f"\n[Node A] Memulai sesi dengan Ka: {ka.decode()}")
    try:
        s_kdc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s_kdc.bind(('127.0.0.2', 0)) 
        s_kdc.connect(('127.0.0.1', 5000))
        n1 = "87654321"
        req_kdc = f"NodeA||NodeB||{n1}".encode('utf-8')
        
        print(f"send: [{req_kdc.decode('utf-8')}]")
        s_kdc.sendall(req_kdc)

        resp = s_kdc.recv(2048)
        print(f"recv: [{resp.hex()}]")
        
        len_b = int.from_bytes(resp[:4], byteorder='big')
        part_b = resp[4:4+len_b]
        part_a = resp[4+len_b:]
        s_kdc.close()

        dec_a = cipher_aes_custom(ka, part_a[8:], nonce=part_a[:8])[8:]
        ks = dec_a[:16]
        print("[Node A] Berhasil mendapatkan Session Key (Ks) dari KDC.")

        s_b = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s_b.bind(('127.0.0.2', 0))
        s_b.connect(('127.0.0.3', 5002))
        
        print(f"send: [{part_b.hex()}]")
        s_b.sendall(part_b)

        enc_n2 = s_b.recv(1024)
        print(f"recv: [{enc_n2.hex()}]")
        
        n2 = cipher_aes_custom(ks, enc_n2[8:], nonce=enc_n2[:8])[8:].decode('utf-8')
        fn2 = str(int(n2) - 1)
        enc_fn2 = encrypt_with_nonce(ks, fn2.encode('utf-8'))
        
        print(f"send: [{enc_fn2.hex()}]")
        s_b.sendall(enc_fn2)
        
        print("\n" + "="*40)
        print(" [SUCCESS] 'Exit' to quit session")
         
        t = threading.Thread(target=receive_chat, args=(s_b, ks), daemon=True)
        t.start()
        
        while True:
            msg = input("[Node A] : ")
            if msg.lower() == 'exit':
                break
            
            enc_msg = encrypt_with_nonce(ks, msg.encode('utf-8'))
            print(f"send: [{enc_msg.hex()}]")
            s_b.sendall(enc_msg)
            
        s_b.close()
    except Exception as e:
        print(f"[ERROR] Proses gagal: {e}\n")

def main():
    print("="*40)
    print("INITIATOR NODE A (IP: 127.0.0.2)    ")
    while True:
        ch = input("Tekan '1' lalu Enter untuk memulai transaksi: ").strip()
        if ch == '1': run_handshake()

if __name__ == '__main__':
    main()