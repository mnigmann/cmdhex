import curses
import os
import sys
import argparse
from os.path import splitext

p = argparse.ArgumentParser()
p.add_argument("filename")
p.add_argument("-f", "--in-format", dest="format", choices=["bin", "hex"], default=None, help="Format of the file being read")
p.add_argument("-o", "--out-format", dest="out", choices=["bin", "hex"], help="Format to use when writing to the file. If unspecified, the input and output formats are assumed to match")
args = p.parse_args()


cursor = 0
mode = ""
nibble = 0
buf = ""
voffs = 0
LINES = COLS = 0
asc = False

if args.format is None:
    file_format = "hex" if splitext(args.filename)[1] in [".hex", ".ihex"] else "bin"
else:
    file_format = args.format

if file_format == "bin":
    with open(args.filename, "rb") as f:
        data = bytearray(f.read())
elif file_format == "hex":
    data = bytearray()
    with open(args.filename) as f:
        cont = f.read().split(":")
        for r in cont[1:]:
            r = r.strip()
            size = int(r[0:2], 16)
            addr = int(r[2:6], 16)
            t = int(r[6:8], 16)
            seg = bytearray(int(r[8+i*2:10+i*2], 16) for i in range(size))
            if t == 0:
                if addr == len(data): data += seg
                elif addr > len(data): data += bytearray([0]*(addr - len(data))) + seg
            elif t == 1:
                break
            

out_format = args.out or file_format

def update_cursor(stdscr):
    global cursor
    cursor = min(len(data), max(0, cursor))
    if asc: stdscr.move(1 + cursor//16 - voffs, 61 + cursor%16)
    else: stdscr.move(1 + cursor//16 - voffs, 10 + 3*(cursor % 16))


def refresh_page(stdscr):
    global cursor, voffs
    cursor = min(len(data), max(0, cursor))
    if cursor//16 - voffs >= LINES - 2:
        voffs = cursor//16 - LINES + 3
    if cursor//16 - voffs < 0:
        voffs = cursor//16
    for r in range(1, LINES - 1):
        x = r - 1 + voffs
        n = min(16, len(data) - x*16)
        if n < 0: stdscr.addstr(r, 0, " "*(COLS-1))
        else: stdscr.addstr(r, 0, hex(16*x)[2:].rjust(8, '0') + "  " + " ".join(hex(data[i])[2:].rjust(2, "0") for i in range(16*x, 16*x+n)).ljust(48, " ") + ("  |"+"".join(chr(x) if (127 > x >= 32 or x >= 0xAD) else '.' for x in data[16*x:16*x+n])+"|").ljust(20, " "))
    update_cursor(stdscr)
    stdscr.refresh()


def gensum(s):
    return s+bytearray([(256-(sum(s)&255))&255])

def tohex(s, sp=0):
    return (" "*sp).join(hex(r)[2:].rjust(2, '0') for r in s)


def main(stdscr):
    global mode, cursor, data, nibble, buf, LINES, COLS, asc
    stdscr.clear()
    LINES, COLS = stdscr.getmaxyx()
    stdscr.addstr(0, 0, "Command line hex editor")
    refresh_page(stdscr)
    while True:
        k = stdscr.getch()
        if k == curses.KEY_RESIZE:
            LINES, COLS = stdscr.getmaxyx()
            continue
        if buf:
            if k == ord("\n"):
                if buf.startswith(":0x"):
                    cursor = int(buf[3:], 16)
                    refresh_page(stdscr)
                else:
                    if "w" in buf:
                        if out_format == "bin":
                            with open(args.filename, "wb") as f: f.write(data)
                        if out_format == "hex":
                            with open(args.filename, "w") as f:
                                f.write(":"+tohex(gensum(b"\x02\x00\x00\x02\x00\x00"))+"\n")
                                for i in range(0, len(data), 16):
                                    n = min(16, len(data) - i)
                                    f.write(":" + tohex(gensum(bytearray([n, i>>8, i&255, 0])+data[i:i+n]))+"\n")
                                f.write(":00000001FF\n")
                    if "q" in buf: break
                buf = ""
            elif k == 27:
                stdscr.addstr(LINES-1, 0, " "*(COLS-1))
                stdscr.refresh()
                update_cursor(stdscr)
                buf = ""
            else:
                buf += chr(k)
                stdscr.addstr(LINES-1, len(buf)-1, chr(k))
                stdscr.refresh()
            continue
        if k == 27: 
            mode = ""
            buf = ""
            stdscr.addstr(LINES-1, 0, "             ")
            update_cursor(stdscr)
            stdscr.refresh()
        if mode == "":
            if k == ord(":") and buf == "":
                buf = ":"
                stdscr.addstr(LINES-1, 0, ":")
                stdscr.refresh()
            elif k == ord("i"):
                mode = "i"
                stdscr.addstr(LINES-1, 0, "-- INSERT -- ")
                update_cursor(stdscr)
                stdscr.refresh()
                nibble = 0
                continue
            elif k == ord("R"):
                mode = "R"
                stdscr.addstr(LINES-1, 0, "-- REPLACE --")
                update_cursor(stdscr)
                stdscr.refresh()
                nibble = 0
                continue
            elif k == ord("\t"):
                asc = not asc
                update_cursor(stdscr)
            elif k == ord("g"):
                cursor = 0
                refresh_page(stdscr)
            elif k == ord("G"):
                cursor = len(data)-1
                refresh_page(stdscr)
        if k == curses.KEY_RIGHT:
            cursor += 1
            refresh_page(stdscr)
        elif k == curses.KEY_LEFT:
            cursor -= 1
            refresh_page(stdscr)
        elif k == curses.KEY_DOWN:
            cursor += 16
            refresh_page(stdscr)
        elif k == curses.KEY_UP:
            cursor -= 16
            refresh_page(stdscr)
        elif k == curses.KEY_NPAGE:
            cursor += 16*(LINES-2)
            refresh_page(stdscr)
        elif k == curses.KEY_PPAGE:
            cursor -= 16*(LINES-2)
            refresh_page(stdscr)
        elif k == 127 or k == curses.KEY_BACKSPACE:
            cursor -= 1
            del data[cursor]
            refresh_page(stdscr)
        elif k < 0: continue
        elif chr(k) in "0123456789abcdefABCDEF" and mode and mode in "iR" and not asc:
            if nibble == 0 and mode == "i":
                data.insert(cursor, 0)
            data[cursor] = (0xff & (data[cursor] << 4)) | int(chr(k), 16)
            if nibble == 1:
                cursor += 1
            refresh_page(stdscr)
            nibble = 1 - nibble
        elif mode and mode in "iR" and asc:
            if mode == "i": data.insert(cursor, k)
            elif cursor < len(data)-1: data[cursor] = k
            cursor += 1
            refresh_page(stdscr)

os.environ.setdefault('ESCDELAY', '25')
curses.wrapper(main)

