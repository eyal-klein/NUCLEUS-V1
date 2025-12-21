import { NucleusOrb } from "@/components/NucleusOrb";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Mic, MicOff, Settings, Terminal } from "lucide-react";
import { useEffect, useRef, useState } from "react";

type Message = {
  role: "user" | "assistant" | "system";
  content: string;
  timestamp: number;
};

export default function Home() {
  const [isConnected, setIsConnected] = useState(false);
  const [state, setState] = useState<"idle" | "listening" | "thinking" | "speaking">("idle");
  const [messages, setMessages] = useState<Message[]>([]);
  const [amplitude, setAmplitude] = useState(0);
  const scrollRef = useRef<HTMLDivElement>(null);

  // Mock connection and state changes for demo
  const toggleConnection = () => {
    if (isConnected) {
      setIsConnected(false);
      setState("idle");
      addMessage("system", "Disconnected from NUCLEUS Core.");
    } else {
      setIsConnected(true);
      setState("listening");
      addMessage("system", "Connected to NUCLEUS Core v3.0");
      addMessage("assistant", "שלום. אני כאן. איך אנחנו מתקדמים היום?");
    }
  };

  const addMessage = (role: Message["role"], content: string) => {
    setMessages((prev) => [
      ...prev,
      { role, content, timestamp: Date.now() },
    ]);
  };

  // Auto-scroll to bottom
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  // Mock amplitude animation
  useEffect(() => {
    if (state === "listening" || state === "speaking") {
      const interval = setInterval(() => {
        setAmplitude(Math.random());
      }, 100);
      return () => clearInterval(interval);
    } else {
      setAmplitude(0);
    }
  }, [state]);

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col overflow-hidden">
      {/* Header */}
      <header className="p-6 flex justify-between items-center z-10">
        <div className="flex items-center gap-3">
          <div className="w-3 h-3 rounded-full bg-primary animate-pulse" />
          <h1 className="text-2xl font-bold tracking-widest font-mono">NUCLEUS</h1>
        </div>
        <Button variant="ghost" size="icon" className="rounded-full hover:bg-primary/10">
          <Settings className="w-5 h-5" />
        </Button>
      </header>

      {/* Main Content */}
      <main className="flex-1 flex flex-col items-center justify-center relative">
        {/* Background Grid */}
        <div className="absolute inset-0 bg-[linear-gradient(to_right,#80808012_1px,transparent_1px),linear-gradient(to_bottom,#80808012_1px,transparent_1px)] bg-[size:24px_24px] pointer-events-none" />

        {/* Central Orb */}
        <div className="z-10 mb-12 scale-150">
          <NucleusOrb state={state} amplitude={amplitude} />
        </div>

        {/* Status Text */}
        <div className="z-10 text-center space-y-2 mb-8">
          <h2 className="text-4xl font-light tracking-tight">
            {state === "idle" && "Ready to Merge"}
            {state === "listening" && "Listening..."}
            {state === "thinking" && "Processing..."}
            {state === "speaking" && "Speaking..."}
          </h2>
          <p className="text-muted-foreground text-sm font-mono">
            {isConnected ? "Secure Link Established" : "System Standby"}
          </p>
        </div>

        {/* Controls */}
        <div className="z-10 flex gap-4">
          <Button
            size="lg"
            variant={isConnected ? "destructive" : "default"}
            className={`rounded-full w-16 h-16 p-0 transition-all duration-500 ${
              isConnected ? "bg-destructive/20 hover:bg-destructive/40" : "bg-primary/20 hover:bg-primary/40"
            } backdrop-blur-md border border-white/10`}
            onClick={toggleConnection}
          >
            {isConnected ? (
              <MicOff className="w-6 h-6" />
            ) : (
              <Mic className="w-6 h-6" />
            )}
          </Button>
        </div>
      </main>

      {/* Transcript / Terminal Panel */}
      <Card className="mx-6 mb-6 h-48 bg-black/40 backdrop-blur-xl border-white/5 overflow-hidden flex flex-col">
        <div className="p-2 border-b border-white/5 flex items-center gap-2 bg-white/5">
          <Terminal className="w-4 h-4 text-muted-foreground" />
          <span className="text-xs font-mono text-muted-foreground">TRANSCRIPT_LOG</span>
        </div>
        <ScrollArea className="flex-1 p-4 font-mono text-sm" ref={scrollRef}>
          {messages.length === 0 ? (
            <div className="text-muted-foreground/50 italic">Waiting for input...</div>
          ) : (
            <div className="space-y-2">
              {messages.map((msg, i) => (
                <div key={i} className={`flex gap-2 ${msg.role === "assistant" ? "text-primary" : msg.role === "system" ? "text-yellow-500" : "text-foreground"}`}>
                  <span className="opacity-50">[{new Date(msg.timestamp).toLocaleTimeString()}]</span>
                  <span className="font-bold uppercase">{msg.role}:</span>
                  <span>{msg.content}</span>
                </div>
              ))}
            </div>
          )}
        </ScrollArea>
      </Card>
    </div>
  );
}
