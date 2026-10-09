#!/usr/bin/env python3
"""Build Mac Automation Doctor Free submission media.

These assets use synthetic sample values and wording tied to the public Free 1.0
report format. They contain no real user paths, LaunchAgents, logs, secrets, or
machine data. They are marketing/review media, not diagnostic evidence.

Requires Pillow plus DejaVu Sans / DejaVu Sans Mono.
"""
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import hashlib, json, textwrap

OUT = Path(__file__).resolve().parent
SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
SANS_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
MONO_B = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"

BG=(17,21,26); PANEL=(27,33,40); PANEL2=(34,41,49); TEXT=(240,244,247)
MUTED=(162,174,187); TEAL=(78,190,180); YELLOW=(240,190,70)
RED=(232,100,95); GREEN=(88,194,130); BORDER=(58,68,80)

def f(path,size): return ImageFont.truetype(path,size)
def rounded(d,box,r,fill,outline=None,width=1):
    d.rounded_rectangle(box,radius=r,fill=fill,outline=outline,width=width)

def header(d,title,subtitle=None,w=1440):
    d.text((72,58),title,font=f(SANS_B,42),fill=TEXT)
    if subtitle: d.text((72,113),subtitle,font=f(SANS,22),fill=MUTED)
    d.text((w-72,70),"CENLUMA",font=f(SANS_B,20),fill=TEAL,anchor="ra")

def terminal(img,xy,size,lines,title):
    x,y=xy; w,h=size; d=ImageDraw.Draw(img)
    rounded(d,(x,y,x+w,y+h),18,PANEL,BORDER,2)
    d.rectangle((x,y,x+w,y+54),fill=PANEL2)
    for i,c in enumerate([(255,95,87),(255,189,46),(39,201,63)]):
        d.ellipse((x+22+i*28,y+19,x+34+i*28,y+31),fill=c)
    d.text((x+120,y+16),title,font=f(SANS,17),fill=MUTED)
    yy=y+76
    for line,color in lines:
        d.text((x+28,yy),line,font=f(MONO,18),fill=color)
        yy += 27

def build_icon():
    img=Image.new("RGBA",(1024,1024),(18,27,31,255)); d=ImageDraw.Draw(img)
    rounded(d,(96,96,928,928),180,(24,59,64,255),(80,190,180,255),8)
    nodes=[(300,350),(512,260),(725,350),(725,620),(512,740),(300,620)]
    for a,b in zip(nodes,nodes[1:]+nodes[:1]): d.line((a,b),fill=(84,112,116,255),width=22)
    for x,y in nodes:
        d.ellipse((x-42,y-42,x+42,y+42),fill=(31,43,48,255),outline=(118,152,155,255),width=8)
    d.line([(215,515),(340,515),(390,430),(455,630),(515,480),(565,540),(620,515),(805,515)],fill=(247,202,77,255),width=30,joint="curve")
    d.ellipse((445,445,579,579),fill=(24,59,64,255),outline=(78,190,180,255),width=10)
    d.line([(480,513),(510,545),(556,482)],fill=(230,250,244,255),width=20)
    img.save(OUT/"mac-automation-doctor-free-icon-1024.png")

def build_summary():
    img=Image.new("RGB",(1440,900),BG); d=ImageDraw.Draw(img)
    header(d,"Mac Automation Doctor Free","Read-only LaunchAgent diagnostics · synthetic sample data")
    lines=[
      ("$ python3 mac_automation_doctor_free.py --stdout",TEAL),("",TEXT),
      ("# Mac Automation Doctor Free Edition Report",TEXT),("Edition: Free (User LaunchAgents Scope)",MUTED),("",TEXT),
      ("## Summary Metrics",YELLOW),("User Services Scanned: 7",TEXT),("Services with Warnings: 2",TEXT),("Plist Parse Failures: 0",TEXT),("",TEXT),
      ("### Severity Breakdown",YELLOW),("CRITICAL: 1",TEXT),("HIGH: 1",TEXT),("MEDIUM: 0",TEXT),("LOW: 0",TEXT),("INFO: 0",TEXT),("",TEXT),
      ("### Warning Counts",YELLOW),("program_path_missing: 1",RED),("duplicate_label: 1",YELLOW),
    ]
    terminal(img,(72,170),(1296,630),lines,"Terminal — synthetic sample")
    d.text((72,830),"Synthetic sample output based on the Free 1.0 report format. No personal paths or machine data.",font=f(SANS,18),fill=MUTED)
    img.save(OUT/"mac-automation-doctor-free-screenshot-01-summary.png")

def build_finding():
    img=Image.new("RGB",(1440,900),BG); d=ImageDraw.Draw(img)
    header(d,"A finding you can act on","Free 1.0 explains what it found and why it matters")
    lines=[
      ("## User Service Findings",YELLOW),("",TEXT),
      ("### Service: `com.example.worker` (user_launch_agent)",TEXT),
      ("- **Plist:** `~/Library/LaunchAgents/com.example.worker.plist`",MUTED),("- **Program:** `~/bin/example-worker`",MUTED),("",TEXT),
      ("#### [CRITICAL] Referenced Executable Missing",RED),("`program_path_missing`",MUTED),("",TEXT),
      ("- **Why this matters:**",YELLOW),("The specified executable path does not exist on disk,",TEXT),("causing launchd spawn failures whenever triggered.",TEXT),("",TEXT),
      ("- **Remediation guidance:**",YELLOW),("Verify the script/executable path, reinstall the missing",TEXT),("executable, or update the plist to the correct path.",TEXT),
    ]
    terminal(img,(72,170),(1296,630),lines,"report.md — synthetic sample")
    d.text((72,830),"Synthetic service name/path; finding title and guidance are based on the Free 1.0 catalog.",font=f(SANS,18),fill=MUTED)
    img.save(OUT/"mac-automation-doctor-free-screenshot-02-finding.png")

def build_safety():
    img=Image.new("RGB",(1440,900),BG); d=ImageDraw.Draw(img)
    header(d,"Diagnose first. Change nothing automatically.","Mac Automation Doctor Free is deliberately conservative.")
    cards=[
      ("READ-ONLY","Inspects user LaunchAgents and local system signals without editing launchd configuration.",GREEN),
      ("NO SUDO","The intended Free scan does not need administrator elevation.",TEAL),
      ("NO TELEMETRY","Diagnostic decisions use no network calls, cloud AI, or remote telemetry.",TEAL),
      ("NO AUTO-REPAIR","It produces local Markdown/JSON reports; you choose what to change.",YELLOW),
    ]
    for i,(title,body,color) in enumerate(cards):
        row=i//2; col=i%2; x=72+col*650; y=190+row*260
        rounded(d,(x,y,x+610,y+220),22,PANEL,BORDER,2)
        d.text((x+30,y+30),title,font=f(MONO_B,22),fill=color)
        yy=y+82
        for line in textwrap.wrap(body,width=48):
            d.text((x+30,yy),line,font=f(SANS,21),fill=TEXT); yy+=31
    d.text((72,770),"Free scope: user LaunchAgents + local resource/runtime snapshot.",font=f(SANS_B,22),fill=TEXT)
    d.text((72,811),"Not a replacement for macOS security controls, MDM, Background Items approval, or manual review.",font=f(SANS,18),fill=MUTED)
    img.save(OUT/"mac-automation-doctor-free-screenshot-03-safety.png")

if __name__ == "__main__":
    build_icon(); build_summary(); build_finding(); build_safety()
    files={}
    for p in sorted(OUT.glob("*.png")):
        files[p.name]={"bytes":p.stat().st_size,"sha256":hashlib.sha256(p.read_bytes()).hexdigest()}
    (OUT/"manifest.json").write_text(json.dumps(files,indent=2)+"\n")
    print(json.dumps(files,indent=2))
