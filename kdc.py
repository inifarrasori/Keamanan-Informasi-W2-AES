import socket
import os
import json
import threading
from aes import cipher_aes_custom

CONFIG_PATH = "keys.json"

def init_config():
    default_keys = {"NodeA": "MasterKeyForA_12", "NodeB": "MasterKeyForB_34"}
    if not os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "w") as f: json.dump(default_keys, f, indent=4)

def get_keys():
    try:
        with open(CONFIG_PATH, "r") as f: return json.load(f)
    except:
        return {"NodeA": "MasterKeyForA_12", "NodeB": "MasterKeyForB_34"}

def socket_server_thread():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('127.0.0.1', 5000))
    server.listen(5)
    
    while True:
        conn, addr = server.accept()
        print(f"\n[KDC] tiket baru dari {addr}...")
        
        #log
        raw_data = conn.recv(1024)
        data = raw_data.decode('utf-8')
        print(f"recv: [{data}]")
        
        id_a, id_b, n1 = data.split("||")
        keys = get_keys()
        ka = keys.get(id_a, "MasterKeyForA_12").encode('utf-8')
        kb = keys.get(id_b, "MasterKeyForB_34").encode('utf-8')

        ks = os.urandom(16)
        msg_b = ks + f"||{id_a}".encode('utf-8')
        part_b = cipher_aes_custom(kb, msg_b)

        msg_a = ks + f"||{id_a}||{id_b}||{n1}".encode('utf-8')
        part_a = cipher_aes_custom(ka, msg_a)

        len_b = len(part_b).to_bytes(4, byteorder='big')
        payload = len_b + part_b + part_a
        
        print(f"send: [{payload.hex()}]")
        conn.sendall(payload)
        
        print("[KDC] Tiket berhasil dibuat dan dikirim")
        conn.close()

def main():
    init_config()
    t = threading.Thread(target=socket_server_thread, daemon=True)
    t.start()
    
    while True:
        keys = get_keys()
        print("\n" + "="*40)
        print("   KDC SERVER (IP: 127.0.0.1:5000)    ")
        print(f"[KUNCI AKTIF]")
        print(f"  - Node A (Ka): {keys.get('NodeA')}")
        print(f"  - Node B (Kb): {keys.get('NodeB')}")
        print("-" * 40)
        print("1. Ubah Kunci Master Ka")
        print("2. Ubah Kunci Master Kb")
        print("3. Refresh")
        print("q. Keluar")
        
        choice = input("Pilih menu (1/2/3/q): ").strip()
        
        if choice == '1':
            new_ka = input("Masukkan Kunci Ka Baru: ").strip()
            if new_ka:
                keys['NodeA'] = new_ka
                with open(CONFIG_PATH, "w") as f: json.dump(keys, f, indent=4)
                print("[SUCCESS] Kunci Ka diperbarui.")
        elif choice == '2':
            new_kb = input("Masukkan Kunci Kb Baru: ").strip()
            if new_kb:
                keys['NodeB'] = new_kb
                with open(CONFIG_PATH, "w") as f: json.dump(keys, f, indent=4)
                print("[SUCCESS] Kunci Kb diperbarui.")
        elif choice == '3':
            continue
        elif choice.lower() == 'q':
            break

if __name__ == '__main__':
    main()