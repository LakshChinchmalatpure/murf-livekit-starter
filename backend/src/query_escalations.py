import sys
import json
import db

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Missing command. Use 'list' or 'update'"}))
        sys.exit(1)
        
    cmd = sys.argv[1]
    if cmd == "list":
        try:
            res = db.get_escalations()
            print(json.dumps(res))
        except Exception as e:
            print(json.dumps({"error": str(e)}))
            sys.exit(1)
            
    elif cmd == "update":
        if len(sys.argv) < 4:
            print(json.dumps({"error": "Missing arguments for update. Usage: update <reference_id> <status>"}))
            sys.exit(1)
        ref_id = sys.argv[2]
        status = sys.argv[3]
        try:
            res = db.update_escalation_status(ref_id, status)
            print(json.dumps(res))
        except Exception as e:
            print(json.dumps({"error": str(e)}))
            sys.exit(1)
            
    else:
        print(json.dumps({"error": f"Unknown command: {cmd}"}))
        sys.exit(1)

if __name__ == "__main__":
    main()
