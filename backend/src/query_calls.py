import sys
import json
import db

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Missing command. Use 'list'"}))
        sys.exit(1)
        
    cmd = sys.argv[1]
    if cmd == "list":
        try:
            res = db.get_calls()
            print(json.dumps(res))
        except Exception as e:
            print(json.dumps({"error": str(e)}))
            sys.exit(1)
    else:
        print(json.dumps({"error": f"Unknown command: {cmd}"}))
        sys.exit(1)

if __name__ == "__main__":
    main()
