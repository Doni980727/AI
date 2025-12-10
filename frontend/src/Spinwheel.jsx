import React, { useEffect, useState, useRef } from "react";

export default function SpinWheel({ options, result, spinning, size = 140, onSpinEnd }) {
    const [rotation, setRotation] = useState(0);
    const rotationRef = useRef(0);
    const segmentAngle = 360 / options.length;

    useEffect(() => {
        if (!spinning || !result) return;

        const index = options.indexOf(result);
        if (index === -1) return;

        const spinAmount = 360 * 5 + index * segmentAngle + segmentAngle / 2 - 90;
        const targetRotation = rotationRef.current + spinAmount;
        rotationRef.current = targetRotation;
        setRotation(targetRotation);

        const timer = setTimeout(() => {
            if (onSpinEnd) onSpinEnd(); // notify App that spin finished
        }, 3200);

        return () => clearTimeout(timer);
    }, [spinning, result, options, onSpinEnd]);

    return (
        <div style={{ position: "relative", width: size, height: size }}>
            <div style={{
                position: "absolute",
                top: -6,
                left: "50%",
                transform: "translate(-50%, -50%) rotate(180deg)",
                width: 0,
                height: 0,
                borderLeft: "10px solid transparent",
                borderRight: "10px solid transparent",
                borderBottom: "18px solid red",
                zIndex: 2,
            }} />

            <div style={{
                width: "100%",
                height: "100%",
                borderRadius: "50%",
                border: "4px solid #333",
                transition: "transform 3s cubic-bezier(0.22, 1, 0.36, 1)",
                transform: `rotate(${rotation}deg)`,
                background: `conic-gradient(${options
                    .map((_, i) => `hsl(${(360 / options.length) * i}, 70%, 60%) ${i * segmentAngle}deg ${(i + 1) * segmentAngle}deg`)
                    .join(",")})`,
            }} />
        </div>
    );
}
