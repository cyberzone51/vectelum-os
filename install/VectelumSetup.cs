using System;
using System.Diagnostics;
using System.IO;
using System.Reflection;
using System.Text;
using System.Threading;
using Microsoft.Win32;

[assembly: AssemblyTitle("VECTELUM Local Setup")]
[assembly: AssemblyProduct("VECTELUM Local")]
[assembly: AssemblyVersion("0.3.0.0")]

static class Setup {
    const string Uri = "vectelum://launch";
    const string Distro = "Ubuntu-24.04";
    const string HomeUrl = "http://127.0.0.1:8080/home";
    const string Guide = "https://vectelum.netlify.app/install-local";
    static readonly string Wsl = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.System), "wsl.exe");
    static readonly string AppDir = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "VECTELUM");
    static string Source() {
        using (Stream s = Assembly.GetExecutingAssembly().GetManifestResourceStream("vectelum-local.py"))
        using (StreamReader r = new StreamReader(s, Encoding.UTF8)) return r.ReadToEnd();
    }
    static int Run(string file, string args, string input, bool quiet) {
        ProcessStartInfo i = new ProcessStartInfo(file, args);
        i.UseShellExecute = false;
        i.RedirectStandardInput = true;
        i.RedirectStandardOutput = quiet;
        i.RedirectStandardError = quiet;
        i.CreateNoWindow = quiet;
        using (Process p = Process.Start(i)) {
            if (input != null) p.StandardInput.Write(input);
            p.StandardInput.Close();
            if (quiet) {
                p.OutputDataReceived += delegate {};
                p.ErrorDataReceived += delegate {};
                p.BeginOutputReadLine(); p.BeginErrorReadLine();
            }
            p.WaitForExit();
            return p.ExitCode;
        }
    }
    static int Linux(string args, bool root, bool quiet) {
        return Run(Wsl, "-d " + Distro + (root ? " -u root" : "") + " -- " + args, null, quiet);
    }
    static bool Ask(string prompt) {
        Console.Write(prompt + " [y/N] ");
        string a = Console.ReadLine();
        return a != null && a.Trim().Equals("y", StringComparison.OrdinalIgnoreCase);
    }
    static void Open(string url) {
        Process.Start(new ProcessStartInfo(url) { UseShellExecute = true });
    }
    static bool HasDistro() {
        return File.Exists(Wsl) && Linux("true", false, true) == 0;
    }
    static bool DockerReady() {
        return Linux("docker --host unix:///var/run/docker.sock info --format {{.ServerVersion}}", true, true) == 0;
    }
    static void EnsureDocker(bool installing) {
        if (DockerReady()) return;
        if (!installing) {
            Linux("service docker start", true, false);
            if (DockerReady()) return;
            throw new Exception("Docker could not start. Run the installer or consult the guide.");
        }
        // Existing engines are never replaced or upgraded automatically.
        bool installed = Linux("sh -c \"command -v dockerd >/dev/null\"", true, true) == 0;
        if (!installed) {
            if (!Ask("Install Ubuntu Docker Engine, Compose, Git, Python and utilities using Ubuntu repositories?"))
                throw new Exception("Installation cancelled.");
            if (Linux("apt-get update", true, false) != 0 ||
                Linux("apt-get install -y docker.io docker-compose-v2 git python3 util-linux", true, false) != 0)
                throw new Exception("Ubuntu package installation failed.");
        }
        Linux("service docker start", true, false);
        if (!DockerReady()) throw new Exception("Docker is unavailable. Check WSL systemd/Docker configuration.");
    }
    static void KeepAlive() {
        ProcessStartInfo i = new ProcessStartInfo(Wsl, "-d " + Distro + " -- flock -n /tmp/vectelum-local-keepalive.lock sleep infinity");
        i.UseShellExecute = false; i.CreateNoWindow = true; i.RedirectStandardInput = true;
        using (Process p = Process.Start(i)) p.StandardInput.Close();
    }
    static bool BackendReady() {
        try {
            using (System.Net.WebClient c = new System.Net.WebClient()) {
                return c.DownloadString("http://127.0.0.1:8080/api/health").Contains("\"ok\"");
            }
        } catch { return false; }
    }
    static void Backend(bool fresh) {
        KeepAlive();
        // Fixed, embedded Python source. No URI or arbitrary command text is passed to WSL.
        string action = fresh ? "backend-fresh" : "backend-start";
        if (Run(Wsl, "-d " + Distro + " -u root -- python3 - " + action, Source(), false) != 0)
            throw new Exception("Backend setup/start failed. Read the output above; existing data was not deleted.");
        if (!BackendReady()) throw new Exception("Command Center cannot be reached from Windows.");
    }
    static void Register() {
        Directory.CreateDirectory(AppDir);
        string exe = Path.Combine(AppDir, "VECTELUM-Local.exe");
        string current = Assembly.GetExecutingAssembly().Location;
        if (!String.Equals(current, exe, StringComparison.OrdinalIgnoreCase)) File.Copy(current, exe, true);
        using (RegistryKey key = Registry.CurrentUser.CreateSubKey(@"Software\Classes\vectelum")) {
            key.SetValue("", "URL:VECTELUM Local");
            key.SetValue("URL Protocol", "");
            using (RegistryKey command = key.CreateSubKey(@"shell\open\command"))
                command.SetValue("", "\"" + exe + "\" \"%1\"");
        }
        string menu = Environment.GetFolderPath(Environment.SpecialFolder.Programs);
        Directory.CreateDirectory(menu);
        File.WriteAllText(Path.Combine(menu, "VECTELUM Local.cmd"), "@echo off\r\n\"" + exe + "\" \"" + Uri + "\"\r\n", Encoding.Default);
    }
    static int Main(string[] args) {
        Console.Title = "VECTELUM Local";
        try {
            if (args.Length == 1 && args[0] == "--self-test") {
                if (!Source().Contains("def fresh_backend")) return 1;
                Console.WriteLine("Embedded backend source: OK");
                return 0;
            }
            if (args.Length == 1 && args[0] == Uri) {
                using (Mutex mutex = new Mutex(false, "Local\\VectelumLocalLaunch")) {
                    if (!mutex.WaitOne(0)) return 0;
                    try {
                        Console.WriteLine("Starting VECTELUM Local...");
                        EnsureDocker(false);
                        Backend(false);
                        Open(HomeUrl);
                        return 0;
                    } finally { mutex.ReleaseMutex(); }
                }
            }
            if (args.Length != 0) return 2;
            Console.WriteLine("VECTELUM Local | Windows setup v0.3.0 | Adaptive AI preview");
            Console.WriteLine("The first installation downloads packages and builds the local backend.");
            Console.WriteLine("Requires WSL2, Ubuntu 24.04 and at least 30 GiB free; 50 GB recommended plus content.");
            if (!HasDistro()) {
                Console.WriteLine("Ubuntu-24.04 WSL distribution not detected.");
                if (File.Exists(Wsl) && Ask("Install WSL2 and Ubuntu 24.04 using Microsoft's WSL installer? Windows will ask for administrator permission")) {
                    using (Process p = Process.Start(new ProcessStartInfo(Wsl, "--install -d Ubuntu-24.04") { UseShellExecute = true, Verb = "runas" })) {
                        p.WaitForExit();
                        Console.WriteLine("WSL installer exit code: " + p.ExitCode);
                    }
                    Console.WriteLine("Restart if requested, open Ubuntu to finish its first-run setup, then run this installer again.");
                } else {
                    Open("https://learn.microsoft.com/windows/wsl/install");
                    Console.WriteLine("Install Ubuntu-24.04 using the official guide, then run this installer again.");
                }
                Console.ReadLine(); return 1;
            }
            Console.WriteLine("1. Connect existing compatible VECTELUM");
            Console.WriteLine("2. Install a fresh VECTELUM (never overwrites existing NOMAD data)");
            Console.Write("Choose 1 or 2: ");
            string mode = Console.ReadLine();
            if (mode != "1" && mode != "2") return 1;
            bool fresh = mode == "2";
            if (!Ask("Continue? This software has Docker socket access; use only on a trusted local machine")) return 1;
            if (fresh) {
                Console.WriteLine("Check available space on the Windows drive hosting WSL before continuing.");
                if (!Ask("I have at least 30 GiB free on the WSL host drive")) return 1;
            }
            EnsureDocker(fresh);
            if (fresh && Linux("sh -c \"command -v git && command -v python3 && docker compose version\"",true,true)!=0) {
                if (!Ask("Install missing Git, Python and Compose packages from Ubuntu repositories?")) return 1;
                if (Linux("apt-get update",true,false)!=0 || Linux("apt-get install -y git python3 docker-compose-v2 util-linux",true,false)!=0)
                    throw new Exception("Prerequisite setup failed.");
            }
            Backend(fresh);
            Register();
            Console.WriteLine("Installed. Launch VECTELUM OS from the website or Start menu.");
            Open(HomeUrl);
            return 0;
        } catch (Exception e) {
            Console.Error.WriteLine("VECTELUM: " + e.Message);
            Console.WriteLine("Guide: " + Guide);
            Console.WriteLine("Press Enter to close.");
            Console.ReadLine(); return 1;
        }
    }
}
