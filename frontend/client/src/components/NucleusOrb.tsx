import { motion } from "framer-motion";
import { useEffect, useState } from "react";

interface NucleusOrbProps {
  state: "idle" | "listening" | "thinking" | "speaking";
  amplitude?: number;
}

export function NucleusOrb({ state, amplitude = 0 }: NucleusOrbProps) {
  const [phase, setPhase] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setPhase((p) => (p + 1) % 360);
    }, 50);
    return () => clearInterval(interval);
  }, []);

  // Base size and color based on state
  const getOrbStyle = () => {
    switch (state) {
      case "listening":
        return {
          scale: 1.2 + amplitude * 0.5,
          color: "var(--primary)",
          glow: "0 0 60px var(--primary)",
        };
      case "thinking":
        return {
          scale: 1.0,
          color: "var(--chart-3)", // Purple
          glow: "0 0 40px var(--chart-3)",
        };
      case "speaking":
        return {
          scale: 1.1 + amplitude * 0.3,
          color: "var(--chart-2)", // Cyan
          glow: "0 0 50px var(--chart-2)",
        };
      default: // idle
        return {
          scale: 1.0,
          color: "var(--muted-foreground)",
          glow: "0 0 20px var(--muted-foreground)",
        };
    }
  };

  const style = getOrbStyle();

  return (
    <div className="relative flex items-center justify-center w-64 h-64">
      {/* Outer Glow Ring */}
      <motion.div
        className="absolute inset-0 rounded-full opacity-20 blur-3xl"
        animate={{
          scale: [1, 1.2, 1],
          opacity: [0.1, 0.3, 0.1],
        }}
        transition={{
          duration: 4,
          repeat: Infinity,
          ease: "easeInOut",
        }}
        style={{
          backgroundColor: style.color,
        }}
      />

      {/* Core Orb */}
      <motion.div
        className="relative w-32 h-32 rounded-full backdrop-blur-md"
        animate={{
          scale: style.scale,
          boxShadow: style.glow,
        }}
        transition={{
          type: "spring",
          stiffness: 300,
          damping: 20,
        }}
        style={{
          background: `radial-gradient(circle at 30% 30%, ${style.color}, transparent)`,
          border: `1px solid ${style.color}40`,
        }}
      >
        {/* Inner texture/movement */}
        <div className="absolute inset-0 rounded-full overflow-hidden opacity-50">
          <motion.div
            className="absolute inset-[-50%]"
            animate={{
              rotate: 360,
            }}
            transition={{
              duration: 10,
              repeat: Infinity,
              ease: "linear",
            }}
            style={{
              background: `conic-gradient(from 0deg, transparent, ${style.color}20, transparent)`,
            }}
          />
        </div>
      </motion.div>

      {/* Orbital Particles */}
      {state !== "idle" && (
        <>
          {[...Array(3)].map((_, i) => (
            <motion.div
              key={i}
              className="absolute w-2 h-2 rounded-full"
              animate={{
                rotate: 360,
                scale: [1, 1.5, 1],
              }}
              transition={{
                duration: 3 + i,
                repeat: Infinity,
                ease: "linear",
                delay: i * 0.5,
              }}
              style={{
                backgroundColor: style.color,
                width: 200 + i * 40, // Orbit radius
                height: 200 + i * 40,
                borderRadius: "50%",
                border: `1px solid ${style.color}20`,
                borderTopColor: style.color,
                borderRightColor: "transparent",
                borderBottomColor: "transparent",
                borderLeftColor: "transparent",
              }}
            />
          ))}
        </>
      )}
    </div>
  );
}
