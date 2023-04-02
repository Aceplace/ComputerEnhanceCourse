import sys

if __name__ == '__main__':
    source_file = sys.argv[1]

    try:
        with open(source_file, "rb") as f:
            byte = f.read(1)
            while byte:
                binary_byte = format(ord(byte), "08b")
                sys.stdout.write(binary_byte + " ")
                byte = f.read(1)
    except FileNotFoundError:
        print(f"Error: File '{source_file}' not found.")
    except Exception as e:
        print(f"Error: {e}")