#!/usr/bin/env python3
"""Diamond Hands Sim Bot — Automated CLI Validation Suite.

Validates:
A) Execution (A.C. Works)
B) Valid Input (A.C. Expected Output)
C) No Stalls (A.C. SLA Compliance)
"""
import subprocess
import time
import os
import sys
import re
import pty

class SimBot:
    def __init__(self):
        # Use --force-interactive for reliable headless validation
        self.cmd = [sys.executable, "main.py", "--force-interactive"]
        self.results = []

    def log(self, msg):
        print(f"🤖 [SIM BOT] {msg}")

    def run_command(self, command: str, expected_keywords: list[str], timeout: float = 60.0):
        self.log(f"Executing: {command}")
        start_time = time.time()
        
        # Using pseudo-terminal to force interactive mode
        master, slave = pty.openpty()
        
        try:
            # We capture stdout/stderr together for simplicity in TUI parsing
            process = subprocess.Popen(
                self.cmd,
                stdin=slave,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                close_fds=True
            )
            os.close(slave)
            
            # Send the command
            time.sleep(4) # Wait for boot
            os.write(master, f"{command}\n".encode())
            
            # Wait for execution (longer for stresstest)
            if command == "/stresstest":
                time.sleep(15)
            else:
                time.sleep(5)
                
            # Send quit
            os.write(master, "/quit\n".encode())
            
            stdout, _ = process.communicate(timeout=timeout)
            duration = time.time() - start_time
            
            # A) Works
            success = (process.returncode == 0)
            
            # B) Valid Input (Case-Insensitive)
            # Remove ANSI codes before matching
            clean_out = re.sub(r'\033\[[0-9;]*m', '', stdout)
            found_keywords = [k for k in expected_keywords if k.lower() in clean_out.lower()]
            valid_output = (len(found_keywords) == len(expected_keywords))
            
            # C) No Stalls
            sla_pass = (duration < timeout)

            result = {
                "command": command,
                "success": success,
                "valid_output": valid_output,
                "sla_pass": sla_pass,
                "duration": duration,
                "missing_keywords": [k for k in expected_keywords if k.lower() not in clean_out.lower()]
            }
            self.results.append(result)
            
            if success and valid_output and sla_pass:
                self.log(f"✅ PASS ({duration:.2f}s)")
            else:
                self.log(f"❌ FAIL: success={success}, valid={valid_output}, sla={sla_pass}")
                if not valid_output:
                    self.log(f"   Missing: {result['missing_keywords']}")
                # print(f"DEBUG OUT: {clean_out}")
                
        except subprocess.TimeoutExpired:
            self.log(f"🛑 STALL DETECTED (> {timeout}s)")
            process.kill()
            self.results.append({"command": command, "success": False, "sla_pass": False, "duration": timeout})
        except Exception as e:
            self.log(f"⚠️ Error: {e}")
        finally:
            try: os.close(master)
            except: pass

    def report(self):
        print("\n" + "="*50)
        print("💎 DIAMOND HANDS ACCEPTANCE REPORT")
        print("="*50)
        all_pass = True
        for r in self.results:
            status = "✅" if (r.get("success") and r.get("valid_output") and r.get("sla_pass")) else "❌"
            print(f"{status} {r['command']:<15} | {r.get('duration', 0):.2f}s")
            if status == "❌": all_pass = False
        print("="*50)
        return all_pass

def main():
    bot = SimBot()
    
    # Acceptance Test Cases
    bot.run_command("/todaysupdate", ["DIAMOND HANDS", "MARKET SNAPSHOT"])
    bot.run_command("/stresstest", ["Resilience Stress Test", "Connection stalled"])
    bot.run_command("/wsb", ["WallStBets", "Sentiment", "Ape Volume"])
    bot.run_command("/risk", ["Defensive Command Center", "Risk & Safety Bounds"])
    bot.run_command("/system", ["Institutional Control Center", "Health Hub"])
    bot.run_command("/analyze", ["DEEP ANALYSIS", "GREEK LEVELS"])
    
    if not bot.report():
        sys.exit(1)

if __name__ == "__main__":
    main()
