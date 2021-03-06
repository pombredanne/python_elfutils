#! /usr/bin/env python
import os
import sys 
import getopt 
import os.path
import pdb
import elfutils
import dwarf
#import cProfile


def print_usage():
    print("usage: readelf.py [option] exectuable")
    print """Options are:
    -d Display the dynamic section (if present)
    -h Display the ELF file header
    -l Display the program headers
    -r Display the relocations (if present)
    -S Display the section's header
    -s Display the symbol table 
    -p Raw dump of a section, followed by the name of section
    """
    exit(2)


def print_dynamic(elf):
    dynamic = elf["dynamic"] 
    strtypes = [elfutils.DT_NEEDED, elfutils.DT_SONAME, elfutils.DT_RPATH]
    for entry in dynamic: 
        tag = entry.keys()[0]
        value = entry.values()[0]
        if tag in strtypes:
            tag = elfutils.dynamic_type[tag]
            print "{:<20}{:<30}".format(tag, value)
        elif tag == elfutils.DT_FLAGS: 
            tag = elfutils.dynamic_type[tag] 
            print "{:<20}{:<30}".format(tag, elfutils.DT_FLAGS_type[value])
        elif tag == elfutils.DT_FLAGS_1: 
            tag = elfutils.dynamic_type[tag] 
            print "{:<20}{:<30}".format(tag, elfutils.DT_FLAGS_1_type[value])
        else:
            tag = elfutils.dynamic_type[tag]
            print "{:<20}{:<16}".format(tag, hex(value))

def print_symbol(elf):
    symtabs = elf["symtabs"]
    verindex = elf["verindex"]
    versym = elf["versym"]
    versymlen = len(versym) - 1
    of = "{:<15}{:<10}{:<10}{:<10}{:<20}" 
    type_table = elfutils.sym_type 
    bind_type_table = elfutils.sym_bind_type
    vis_type_table = elfutils.sym_vis_type 
    for symtab in symtabs:
        print "in", symtab
        print of.format("addr", "type", "visiblity", "bind", "name")
        for i, symbol in enumerate(symtabs[symtab]): 
            value = hex(symbol["st_value"])
            name = symbol["st_name"] 
            sym_type = type_table[symbol["st_type"]].split("_")[-1] 
            bind_type = bind_type_table[symbol["st_bind"]].split("_")[-1] 
            vis_type =  vis_type_table[symbol["st_other"]].split("_")[-1] 
            if i <= versymlen: 
                if versym[i] > 1:
                    try:
                        vernaux = verindex[versym[i]] 
                        name += "@"+vernaux["vna_name"]
                    except KeyError:
                        pass 
            print of.format(value, sym_type, vis_type, bind_type, name)
        print "\n"

def print_pheader(elf):
    pheader = elf['programs']
    of = "{:<10}{:<10}{:<10}{:<10}{:<10}{:<10}{:<10}{:<5}" 
    print of.format("Type", "Align", "Offset", "VirtAddr", "PhysAddr", "FileSize", "MemSize", "Flags")
    for entry in pheader:
        try:
            ptype = elfutils.ph_type[entry['p_type']].split("_")[-1]
        except:
            pdb.set_trace()
        flag = elfutils.ph_flags[entry['p_flags']]
        offset = hex(entry['p_offset'])
        virt = hex(entry['p_vaddr'])
        phys = hex(entry['p_paddr'])
        filesize = hex(entry['p_filesz'])
        memsize = hex(entry['p_memsz'])
        align = hex(entry['p_align'])
        print of.format(ptype, align, offset, virt, phys, filesize, memsize, flag)
    if elf['interpreter']:
        print "INTERP: ", elf['interpreter']
    print "\n"

def print_sheader(elf):
    sections = elf['sections']
    of = "{:<20}{:<15}{:<10}{:<10}\n\t\t{:<10}{:<10}{:<10}{:<10}{:<10}{:<20}"
    print of.format("Name", "Type", "Addr", "Offset", "Size", "Link", "Info", "Align", "Entsize", "Flag",) 
    for entry in sections:
        name = entry['sh_name']
        type = elfutils.sh_type[entry['sh_type']]
        flag = elfutils.decide_shflags(entry['sh_flags'])
        addr = hex(entry['sh_addr'])
        offset = hex(entry['sh_offset'])
        size = hex(entry['sh_size'])
        link = hex(entry['sh_link'])
        info = hex(entry['sh_info'])
        align = hex(entry['sh_addralign'])
        entsize = hex(entry['sh_entsize'])
        print of.format(name, type, addr, offset, size, link, info, align, entsize,  flag)
    print "\n"

def print_header(elf):
    header = elf['elf_header']
    print "in elf header:"
    of = "{:<30}{:<20}"
    print of.format("file ident:", elfutils.elf_class_type[header['file_class']]) 
    print of.format("file encoding:", elfutils.elf_encoding[header['file_encoding']])
    print of.format("file version:", header['file_version'])
    print of.format("elf type:", elfutils.elf_type[header['e_type']])
    print of.format("elf machine type:", elfutils.elf_arch_type[header['e_machine']])
    print of.format("elf version:", header['e_version'])
    print of.format("elf entry:", hex(header['e_entry']))
    print of.format("program header offset:", hex(header['e_phoff']))
    print of.format("section header offset:", hex(header['e_shoff']))
    print of.format("elf flags:", header['e_flags'])
    print of.format("elf header size:", header['e_ehsize'])
    print of.format("program entry size:", header['e_phentsize'])
    print of.format("program entry number:", header['e_phnum'])
    print of.format("section entry size:", header['e_shentsize'])
    print of.format("section entry number:", header['e_shnum'])
    print of.format("index of .strtab:", header['e_shstrndx'])
    
def print_rela(elf):
    symtab = elf["symtabs"][".dynsym"] 
    rel_type = elfutils.rel_type
    if "rel" in elf:
        of = "{:<15}{:<20}{:<10}{:<10}" 
        for name, rel in elf["rel"].iteritems(): 
            print "in", name
            print of.format("offset", "type", "Sym.Index",  "Sym.Name") 
            for item in rel: 
                print of.format(hex(item["r_offset"]), rel_type[item["r_type"]],
                        item["r_symbol"], symtab[item["r_symbol"]][0])
    if "rela" in elf:       
        of = "{:<10}{:<15}{:<10}{:<10}{:<10}" 
        for name, rela in elf["rela"].iteritems(): 
            print "in", name 
            print of.format("offset", "type", "Addend",
                    "Sym.Index", "Sym.Name") 
            for item in rela: 
                print of.format(hex(item["r_offset"]), rel_type[item["r_type"]],
                    hex(item["r_addend"]), item["r_symbol"], symtab[item["r_symbol"]]["st_name"]) 


def print_ver(elf):
    print "Symbol Version Table:"
    of = "{:<15}{:<20}{:<15}"     
    print of.format("INDEX", "HASH",  "NAME")
    verindex = elf["verindex"]
    verneed = elf["verneed"] 
    pdb.set_trace()
    for i in elf["versym"]:
        if i == 0: 
            print of.format(i, "LOCAL", "")
        elif i == 1:    
            print of.format(i, "GLOBAL", "")
        else: 
            try:
                entry = verindex[i] 
            except:
                pdb.set_trace()
            print of.format(i, hex(entry["vna_hash"]), entry["vna_name"])
    print "LOCAL ->  The symbol is local, not available outside the object"
    print "GLOBAL -> This symbol is defined in this object and is globally available\n"
    print "all indexes available:"
    of = "{:<15}{:<20}{:<15}{:<15}" 
    of2 = "\t{:<15}{:<15}{:<20}{:<15}{:<15}" 
    print of.format("NUM", "FILE", "VERSION", "ENTRIES")
    for i,v in enumerate(verneed):
        print of.format(i, v["vn_file"], v["vn_version"], v["vn_cnt"]) 
        print of2.format("NUM", "INDEX", "NAME", "HASH", "FLAGS") 
        for i, k in enumerate(v["vernaux"]):
            print of2.format(i, k["vna_other"], k["vna_name"], hex(k["vna_hash"]), k["vna_flags"])
        print ""


def print_dwarf_info(elf):
    pass

def hex_dump(data):
    out_write = sys.stdout.write 
    for index, byte in enumerate(bytearray(data)):        
        byte = hex(byte)[2:]
        if len(byte) == 1:
            byte = byte.zfill(2) 
        if not (index % 16):
            out_write("".join(("\n", hex(index)[2:].zfill(6), ": ", byte)))
        else:
            out_write("".join((" ", byte))) 

def text_dump(data):
    import string
    out_write = sys.stdout.write 
    printable = string.printable 
    for index, byte in enumerate(data): 
        if byte not in printable: 
            try:
                byte = hex(byte)
            except TypeError:
                byte = "0x00"
        if not (index % 32): 
            out_write("".join(("\n", hex(index)[2:].zfill(6), ": ", byte)))
        else: 
            out_write("".join((" ", byte)))
        

def print_section_data(elf, *args): 
    if not elf["target"]:
        raise Exception("reqeuest for section failed")
    data = elf["target"] 
    section = args[1]
    print "section: ", section 
    if section in (".comment", ".strtab"):
        text_dump(data) 
    else:
        hex_dump(data)    
    print "\n"      



def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "dhlrpsSvw:")
    except getopt.GetoptError, err:        
        print str(err)
        print_usage() 
    if len(args) == 0:
        print_usage()
    path = args[0] 
    if not os.path.exists(path):
        print_usage()
    header = False
    dynamic = False
    pheader = False
    sheader =False
    symbol = False 
    dwarf_info = False
    rela = False
    print_section = False
    flags = 0 
    ver = False
    for o, a in opts:
        if o == "--help":
            print_usage()
        elif o == "-d":
            dynamic = True
            flags |= elfutils.ELF_DYNAMIC
        elif o == "-h":  
            header = True
        elif o == "-l":
            pheader = True
        elif o == "-s":
            symbol = True
            flags |= elfutils.ELF_SYMBOL
        elif o == "-S":
            sheader = True 
        elif o == "-w":
            if a == "i":
                dwarf_info = True 
                flags |= elfutils.DWARF_INFO
        elif o == "-r":
            rela = True
            flags |= elfutils.ELF_RELA
        elif o == "-p":
            print_section = True 
            flags |= elfutils.ELF_PSECTION 
            if len(args) < 2:
                print_usage()
                assert False, "option -p requires more args"
        elif o == "-v":
            ver = True
            flags |= elfutils.ELF_VERNEED
        else:
            assert False, "unhandled options" 
    #cProfile.runctx("elfutils.set_target(path)", globals(), locals(), "readelf.trace")    
    elf = elfutils.readelf(path, flags, *args) 
    if dynamic: 
        print_dynamic(elf)
    if header: 
        print_header(elf)
    if pheader: 
        print_pheader(elf)
    if sheader: 
        print_sheader(elf)
    if symbol: 
        print_symbol(elf)
    if rela: 
        print_rela(elf)
    if dwarf_info: 
        print_dwarf_info(elf)
    if print_section: 
        print_section_data(elf, *args)
    if ver: 
        print_ver(elf)

if __name__ == "__main__":
    main()
