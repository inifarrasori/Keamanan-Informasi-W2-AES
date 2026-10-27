import socket
import json
import threading
import sys
from aes import cipher_aes_custom, encrypt_with_nonce

CONFIG_PATH = "keys.json"

def get_kb():
    try:
        with open(CONFIG_PATH, "r") as f: return json.load(f).get("NodeB", "MasterKeyForB_34").encode('utf-8')
    except:
        return b"MasterKeyForB_34"

def receive_chat(conn, ks):
    while True:
        try:
            data = conn.recv(1024)
            if not data:
                print("\n[Sistem] Koneksi terputus dari Node A.")
                break
            
            #log
            print(f"\nrecv: [{data.hex()}]")

            #============= CIPHER
            dec_msg = cipher_aes_custom(ks, data[8:], nonce=data[:8])[8:].decode('utf-8')
            print(f"[Node A] : {dec_msg}")
            
            print("[Node B] : ", end="")
            sys.stdout.flush()
        except Exception as e:
            break

def listen_responder():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('127.0.0.3', 5002))
    server.listen(5)
    
    print("="*40)
    print("RESPONDER NODE B (IP: 127.0.0.3)    ")

    while True:
        print("[Node B] Menunggu koneksi...")
        conn, addr = server.accept()
        kb = get_kb()
        
        try:
            data = conn.recv(1024)
            print(f"recv: [{data.hex()}]")
            
            decrypted_b = cipher_aes_custom(kb, data[8:], nonce=data[:8])[8:]
            ks = decrypted_b[:16]
            id_a = decrypted_b[18:].decode('utf-8')

            n2 = "12345678"
            enc_n2 = encrypt_with_nonce(ks, n2.encode('utf-8'))
            
            print(f"send: [{enc_n2.hex()}]")
            conn.sendall(enc_n2)

            data_fn2 = conn.recv(1024)
            print(f"recv: [{data_fn2.hex()}]")
            
            dec_fn2 = cipher_aes_custom(ks, data_fn2[8:], nonce=data_fn2[:8])[8:].decode('utf-8')
            
            if dec_fn2 == str(int(n2) - 1):
                print("\n" + "="*40)
                print(" [SUCCESS] 'Exit' to quit session")

                
                t = threading.Thread(target=receive_chat, args=(conn, ks), daemon=True)
                t.start()
                
                while True:
                    msg = input("[Node B] : ")
                    if msg.lower() == 'exit':
                        break
                    
                    enc_msg = encrypt_with_nonce(ks, msg.encode('utf-8'))
                    print(f"send: [{enc_msg.hex()}]")
                    conn.sendall(enc_msg)
            else:
                print("[Node B] Autentikasi GAGAL! Nilai tantangan tidak cocok.\n")

        except Exception as e:
            print(f"[ERROR] Tiket tidak valid atau koneksi tertutup.\n")
        finally:
            conn.close()

if __name__ == '__main__':
    listen_responder()