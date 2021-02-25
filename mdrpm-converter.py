import os, sys, shutil, glob, json, zipfile, re
import os.path as path

import tkinter as tk
import tkinter.ttk as ttk
import tkinter.filedialog as filedialog
import tkinter.messagebox as messagebox

def set_entry(entry, text):
    entry.delete(0, tk.END)
    entry.insert(0, text)

# Should put this into fpclib or make it into it's own library
def merge(src, dst):
    for src_dir, dirs, files in os.walk(src):
        # Handle folder
        dst_dir = src_dir.replace(src, dst, 1)
        if path.isfile(dst_dir): os.remove(dst_dir)
        if not path.isdir(dst_dir): os.makedirs(dst_dir, exist_ok=True)
        
        # Handle files
        for f in files:
            sfj = path.join(src_dir, f)
            dfj = path.join(dst_dir, f)
            if path.isdir(dfj): shutil.rmtree(dfj)
            if path.isfile(dfj): os.remove(dfj)
            shutil.copyfile(sfj, dfj)
    shutil.rmtree(src)


class Mainframe(tk.Tk):
    def __init__(self):
        # Create window
        super().__init__()
        self.minsize(645, 600)
        self.title("Minecraft Data and Resource Pack to Mod Converter")
        self.protocol("WM_DELETE_WINDOW", self.exit_window)
        for i in range(1,3):
            self.rowconfigure(i, weight=1)
        self.columnconfigure(0, weight=1)
        
        # Metadata
        mframe = tk.Frame(self)
        mframe.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        mframe.columnconfigure(1, weight=1)
        
        ltexts = ["Name:", "Mod ID:", "Version:", "Description:", "Authors (CSVs):", "License:"]
        self.entries = []
        # Make labels and entries (automagically!)
        for i in range(6):
            label = ttk.Label(mframe, text=ltexts[i])
            label.grid(row=i, column=0)
            entry = ttk.Entry(mframe)
            entry.grid(row=i, column=1, sticky="ew")
            self.entries.append(entry)
        
        # Dependencies, Datapacks, and Resource Packs
        ltexts = ["Mod Dependencies", "Packs"]
        btexts = ["Add", "Replace", "Remove"]
        bcmds = [[lambda: self.add(0), lambda: self.replace(0), lambda: self.remove(0)],
                 [lambda: self.add(1), lambda: self.replace(1), lambda: self.remove(1)]]
        self.frames = []
        self.lboxes = []
        self.lentries = []
        for i in range(2):
            # Create frame
            f = tk.Frame(self)
            f.grid(row=i+1, column=0, sticky="nsew", padx=5, pady=5)
            f.rowconfigure(1, weight=1)
            f.columnconfigure(0, weight=1)
            self.frames.append(f)
            
            # Create label
            label = ttk.Label(f, text=ltexts[i])
            label.grid(row=0, column=0, sticky="nsew")
            
            # Create box for listed things
            lb = tk.Listbox(f, exportselection=False)
            lb.grid(row=1, column=0, sticky="nsew")
            self.lboxes.append(lb)
            
            # The people who implemented scrollbars didn't do a good job.
            # They're slow, don't auto-hide, and cause issues when modifying the listbox.
            #vsb = ttk.Scrollbar(lb, orient="vertical")
            #vsb.config(command=lb.yview)
            #vsb.pack(side="right", fill="y")
            
            #hsb = ttk.Scrollbar(lb, orient="horizontal")
            #hsb.config(command=lb.xview)
            #hsb.pack(side="bottom", fill="x")
            
            # Bottom frame
            self.b = tk.Frame(f)
            self.b.grid(row=2, column=0, sticky="ew", pady=2)
            self.b.columnconfigure(0, weight=1)
            
            # Entry
            entry = ttk.Entry(self.b)
            entry.grid(row=0, column=0, sticky="ew", padx=1)
            self.lentries.append(entry)
            
            # Buttons
            for j in range(3):
                button = ttk.Button(self.b, text=btexts[j], command=bcmds[i][j], width=7)
                button.grid(row=0, column=j+1)
        
        # Listboxes binding
        self.lboxes[0].bind("<<ListboxSelect>>", lambda e: self.edit(0, e))
        self.lboxes[1].bind("<<ListboxSelect>>", lambda e: self.edit(1, e))
        
        # Button for packs to open file selection dialog
        offrame = tk.Frame(self)
        offrame.grid(row=3, column=0, pady=5)
        
        fopen_button = ttk.Button(offrame, text="Add Zip(s)", command=self.open_zip, width=10)
        fopen_button.grid(row=0, column=0)
        fopen_button = ttk.Button(offrame, text="Add Folder", command=self.open_folder, width=12)
        fopen_button.grid(row=0, column=1)
        fopen_button = ttk.Button(offrame, text="Add Contents", command=self.open_contents, width=12)
        fopen_button.grid(row=0, column=2)
        
        # Bottom frame for IO and such
        bframe = tk.Frame(self, pady=5)
        bframe.grid(row=4, column=0)
        
        # Mcmeta Version
        mcmeta = tk.Label(bframe, text="Mcmeta:")
        mcmeta.grid(row=0, column=0)
        self.mcmeta = ttk.Entry(bframe)
        self.mcmeta.insert(0, "6")
        self.mcmeta.grid(row=0, column=1)
        
        # Button for Forge or Fabric
        self.mlf = tk.IntVar(self, 2)
        self.forge = tk.Radiobutton(bframe, text="Forge", variable=self.mlf, value=0)
        self.forge.grid(row=0, column=2)
        self.fabric = tk.Radiobutton(bframe, text="Fabric", variable=self.mlf, value=1)
        self.fabric.grid(row=0, column=3)
        self.fabric = tk.Radiobutton(bframe, text="Both", variable=self.mlf, value=2)
        self.fabric.grid(row=0, column=4)
        
        # Load and export button
        load = ttk.Button(bframe, text="Load", command=self.load, width=7)
        load.grid(row=0, column=5)
        save = ttk.Button(bframe, text="Save", command=self.save, width=7)
        save.grid(row=0, column=6)
        export = ttk.Button(bframe, text="Convert", command=self.export, width=7)
        export.grid(row=0, column=7)
        
        # Associate file extension .mcpc buttons
        #fbframe = tk.Frame(self)
        #fbframe.grid(row=5, column=0, pady=5)
        
        #register = ttk.Button(fbframe, text="Register MCPC Files", command=self.register)
        #register.grid(row=0, column=0)
        #unregister = ttk.Button(fbframe, text="Unregister MCPC Files", command=self.unregister)
        #unregister.grid(row=0, column=1)
    
    def get_entry(self, n):
        return self.entries[n].get()
    
    def edit(self, ln, e):
        box = e.widget
        c = box.curselection()
        if c:
            set_entry(self.lentries[ln], box.get(c[0]))
    
    def add(self, ln):
        text = self.lentries[ln].get().strip()
        if text:
            box = self.lboxes[ln]
            c = box.curselection()
            if c:
                box.selection_clear(c[0])
                box.insert(c[0]+1, text)
                box.selection_set(c[0]+1)
            else:
                box.insert(tk.END, text)
                box.selection_set(box.size()-1)
    
    def replace(self, ln):
        text = self.lentries[ln].get().strip()
        if text:
            box = self.lboxes[ln]
            c = box.curselection()
            if c:
                box.delete(c[0])
                box.insert(c[0], text)
                box.selection_set(c[0])
    
    def remove(self, ln):
        box = self.lboxes[ln]
        c = box.curselection()
        if c:
            box.delete(c[0])
            if box.size() > c[0]:
                box.selection_set(c[0])
            elif box.size():
                box.selection_set(box.size()-1)
            else:
                set_entry(self.lentries[ln], box.get(c[0]))
    
    def open_zip(self):
        files = filedialog.askopenfilenames(parent=self, filetypes=[("Data & Resource Packs", "*.zip")])
        for file in files: self.lboxes[1].insert(tk.END, file)
    
    def open_folder(self):
        directory = filedialog.askdirectory(parent=self)
        self.lboxes[1].insert(tk.END, directory)
    
    def open_contents(self):
        directory = filedialog.askdirectory(parent=self)
        if directory:
            for f in glob.glob(directory+"/*"):
                self.lboxes[1].insert(tk.END, f)
    
    def load(self):
        file = filedialog.askopenfilename(parent=self, filetypes=[("Minecraft Pack Conversion File", ".mcpc .json")])
        if file: self._load(file)
    
    def _load(self, file, silent=False):
        try:
            with open(file, "r") as f:
                # Load json
                data = json.load(f)
                
            keys = ["name", "modid", "ver", "desc", "authors", "license"]
            # Entries at the top
            for i in range(6):
                set_entry(self.entries[i], str(data.get(keys[i], "")))
            
            # Dependencies and Packs
            lists = data.get("lists", [[],[]])
            entries = data.get("entries", ["", ""])
            for i in range(2):
                # Set listbox
                box = self.lboxes[i]
                for v in lists[i]:
                    box.insert(tk.END, v)
                # Set entry content
                set_entry(self.lentries[i], entries[i])
            
            # Modloader stuff
            set_entry(self.mcmeta, str(data.get("mcmeta", 6)))
            mlf = int(data.get("mlf", 2))
            self.mlf.set(mlf)
        
        except Exception as e:
            if not silent: messagebox.showerror(message=f"Error parsing file:\n{type(e).__name__}: {e}")
    
    def save(self):
        file = filedialog.asksaveasfilename(parent=self, filetypes=[("Minecraft Pack Conversion File", ".mcpc .json")])
        if file:
            if len(file) < 5 or file[-5:] not in [".mcpc", ".json"]: file += ".mcpc"
            self._save(file)
    
    def _save(self, file, silent=False):
        try:
            data = {}
            
            keys = ["name", "modid", "ver", "desc", "authors", "license"]
            # Entries at the top
            for i in range(6):
                data[keys[i]] = self.get_entry(i)
            
            # Dependencies and Packs
            lists = [[],[]]
            entries = []
            for i in range(2):
                # Save listbox
                box = self.lboxes[i]
                for v in box.get(0, tk.END):
                    lists[i].append(v)
                # Save entry content
                entries.append(self.lentries[i].get())
            data["lists"] = lists
            data["entries"] = entries
            
            # Modloader stuff
            mcmeta = self.mcmeta.get()
            if mcmeta.isdigit(): data["mcmeta"] = int(mcmeta)
            else:
                set_entry(self.mcmeta, "6")
                data["mcmeta"] = 6
            data["mlf"] = self.mlf.get()
            
            # Save json
            with open(file, "w") as f:
                json.dump(data, f)
        
        except Exception as e:
            if not silent: messagebox.showerror(message=f"Error parsing file:\n{type(e).__name__}: {e}")
    
    def export(self):
        modid = self.get_entry(1)
        
        fname = modid + "-" + self.get_entry(2)
        while path.exists(fname+".jar"): fname += "_"
        
        # Get modloader
        mlf = self.mlf.get()
        # Create temp folder
        if path.isfile("mdrpmc-temp"): os.remove("mdrpmc-temp")
        elif path.isdir("mdrpmc-temp"): shutil.rmtree("mdrpmc-temp")
        os.mkdir("mdrpmc-temp")
        os.chdir("mdrpmc-temp")
        
        # Common to forge and fabric
        os.mkdir("META-INF")
        with open("META-INF/MANIFEST.MF", "w") as file:
            file.write("Manifest-Version: 1.0\n\n")
        
        if mlf > 0: # Using fabric
            # Fabric metadata
            depends = {"fabric-api-base": "*"}
            data = {
                "schemaVersion": 1,
                "authors": [x.strip() for x in self.get_entry(4).split(",")],
                "environment": "*",
                "depends": depends
            }
            
            # Autoform some metadata
            autokeys = [("name", 0), ("id", 1), ("version", 2), ("description", 3), ("license", 5)]
            for k, i in autokeys: data[k] = self.get_entry(i)
            
            # Compile dependencies
            for v in self.lboxes[0].get(0, tk.END):
                # Only use fabric dependencies
                if v.startswith("fo'"): continue
                
                if v.startswith("fa'"):
                    d = v[3:].split(":")
                else:
                    d = v.split(":")
                if len(d) == 2: depends[d[0].strip()] = d[1].strip()
            
            # Write file
            with open("fabric.mod.json", "w") as file:
                json.dump(data, file)
        
        if (mlf+1) % 2: # Using forge
            # Minimal mod entry point (required to make the mod valid)
            with open("Entry.class", "wb") as file:
                # Java bytecode
                file.write(b"\xCA\xFE\xBA\xBE\x00\x00\x00\x34\x00\x14\x01\x00\x05\x45\x6E\x74\x72\x79\x07\x00\x01\x01\x00\x10\x6A\x61\x76\x61\x2F\x6C\x61\x6E\x67\x2F\x4F\x62\x6A\x65\x63\x74\x07\x00\x03\x01\x00\x0A\x45\x6E\x74\x72\x79\x2E\x6A\x61\x76\x61\x01\x00\x23\x4C\x6E\x65\x74\x2F\x6D\x69\x6E\x65\x63\x72\x61\x66\x74\x66\x6F\x72\x67\x65\x2F\x66\x6D\x6C\x2F\x63\x6F\x6D\x6D\x6F\x6E\x2F\x4D\x6F\x64\x3B\x01\x00\x05\x76\x61\x6C\x75\x65\x01\x00")
                # Substitute length of modid and modid
                file.write(bytes([len(modid)]))
                file.write(modid.encode())
                # More Java bytecode
                file.write(b"\x01\x00\x06\x3C\x69\x6E\x69\x74\x3E\x01\x00\x03\x28\x29\x56\x0C\x00\x09\x00\x0A\x0A\x00\x04\x00\x0B\x01\x00\x04\x74\x68\x69\x73\x01\x00\x07\x4C\x45\x6E\x74\x72\x79\x3B\x01\x00\x04\x43\x6F\x64\x65\x01\x00\x0F\x4C\x69\x6E\x65\x4E\x75\x6D\x62\x65\x72\x54\x61\x62\x6C\x65\x01\x00\x12\x4C\x6F\x63\x61\x6C\x56\x61\x72\x69\x61\x62\x6C\x65\x54\x61\x62\x6C\x65\x01\x00\x0A\x53\x6F\x75\x72\x63\x65\x46\x69\x6C\x65\x01\x00\x19\x52\x75\x6E\x74\x69\x6D\x65\x56\x69\x73\x69\x62\x6C\x65\x41\x6E\x6E\x6F\x74\x61\x74\x69\x6F\x6E\x73\x00\x21\x00\x02\x00\x04\x00\x00\x00\x00\x00\x01\x00\x01\x00\x09\x00\x0A\x00\x01\x00\x0F\x00\x00\x00\x2F\x00\x01\x00\x01\x00\x00\x00\x05\x2A\xB7\x00\x0C\xB1\x00\x00\x00\x02\x00\x10\x00\x00\x00\x06\x00\x01\x00\x00\x00\x05\x00\x11\x00\x00\x00\x0C\x00\x01\x00\x00\x00\x05\x00\x0D\x00\x0E\x00\x00\x00\x02\x00\x12\x00\x00\x00\x02\x00\x05\x00\x13\x00\x00\x00\x0B\x00\x01\x00\x06\x00\x01\x00\x07\x73\x00\x08")
            
            # Mcmeta file (because forge is a dum-dum and wants one)
            with open("pack.mcmeta", "w") as file:
                file.write('{"pack": {"description": "", "pack_format": ' + str(self.mcmeta.get()) + '}}')
            
            # Forge metadata
            with open("META-INF/mods.toml", "w") as file:
                file.write(f"""
modLoader = "javafml"
loaderVersion = "[1,)"
license = "{self.get_entry(5)}"

[[mods]]
modId = "{modid}"
version = "{self.get_entry(2)}"
displayName = "{self.get_entry(0)}"
authors = "{self.get_entry(4)}"
description = '''
{self.get_entry(3)}
'''
""")
                for v in self.lboxes[0].get(0, tk.END):
                    # Only use forge dependencies
                    if v.startswith("fa'"): continue
                
                    if v.startswith("fo'"):
                        d = v[3:].split(":")
                    else:
                        d = v.split(":")
                    file.write(f"""
[[dependencies.{modid}]]
modId = "{d[0].strip()}"
mandatory = true
versionRange = "{d[1].strip()}"
ordering = "AFTER"
side = "BOTH"
""")
        
        # Both fabric and forge need packs compiled into two lump folders
        for packloc in self.lboxes[1].get(0, tk.END):
            if packloc.endswith(".zip"):
                # Copy assets or data folders from zip to temp folder
                with zipfile.ZipFile(packloc) as pack:
                    pack.extractall("t")
                
                # Move folders to the proper place in the temp folder
                if path.isdir("t/assets"): merge("t/assets", "assets")
                if path.isdir("t/data"): merge("t/data", "data")
                
                # Deal with people who think exporting zips containing the datapack inside a folder is okay
                # (it's not >:(, get your flippin' datapacks correct!!!!!)
                for f in glob.glob("t/*/assets"): merge(f, "assets")
                for f in glob.glob("t/*/data"): merge(f, "data")
                
                # Delete unused extra files
                shutil.rmtree("t")
            elif path.isdir(packloc):
                # Copy assets or data folders from folder to temp folder
                assets = path.join(packloc, "assets")
                data = path.join(packloc, "data")
                if path.isdir(assets): shutil.copytree(assets, "assets", dirs_exist_ok=True)
                if path.isdir(data): shutil.copytree(data, "data", dirs_exist_ok=True)
        
        # Turn temp folder into jar file
        os.chdir("..")
        if path.isfile(fname+".zip"): os.remove(fname+".zip")
        elif path.isdir(fname+".zip"): shutil.rmtree(fname+".zip")
        shutil.make_archive(fname, "zip", "mdrpmc-temp")
        os.rename(fname+".zip", fname+".jar")
        
        # Delete temp folder
        shutil.rmtree("mdrpmc-temp")
        
        # Show DONE window
        messagebox.showinfo(message=f"Conversion was successful.\nLook for {fname}.jar near the program executable.")
    
    def exit_window(self):
        self._save("auto.mcpc", True)
        self.destroy()

class AutoScrollbar(ttk.Scrollbar):
    def set(self, low, high):
        if float(low) <= 0.0 and float(high) >= 1.0:
            self.tk.call("grid", "remove", self)
        else:
            self.grid()
        ttk.Scrollbar.set(self, low, high)

if __name__ == "__main__":
    m = Mainframe()
    if len(sys.argv) > 1:
        m._load(sys.argv[1])
        if len(sys.argv) > 2:
            m.export()
            exit()
    else:
        m._load("auto.mcpc", True)
    m.mainloop()