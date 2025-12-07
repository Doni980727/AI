import React, { useState } from "react";

const API_BASE = "http://127.0.0.1:8000";

function App() {
  // Persona A
  const [spinA, setSpinA] = useState(null);
  const [scenarioA, setScenarioA] = useState("");
  const [loadingA, setLoadingA] = useState(false);

  // Persona B
  const [spinB, setSpinB] = useState(null);
  const [scenarioB, setScenarioB] = useState("");
  const [loadingB, setLoadingB] = useState(false);

  // Comparison
  const [comparison, setComparison] = useState("");
  const [loadingCompare, setLoadingCompare] = useState(false);

  const [error, setError] = useState("");

  async function callJson(url, options = {}) {
    const res = await fetch(url, {
      headers: { "Content-Type": "application/json" },
      ...options,
    });
    if (!res.ok) throw new Error(`API error: ${res.status}`);
    return res.json();
  }

  // --- SPIN HANDLERS ---

  const handleSpinA = async () => {
    try {
      setError("");
      setScenarioA("");
      const data = await callJson(`${API_BASE}/api/spin`, {
        method: "POST",
        body: "{}",
      });
      setSpinA(data);
    } catch (err) {
      setError(err.message);
    }
  };

  const handleSpinB = async () => {
    try {
      setError("");
      setScenarioB("");
      const data = await callJson(`${API_BASE}/api/spin`, {
        method: "POST",
        body: "{}",
      });
      setSpinB(data);
    } catch (err) {
      setError(err.message);
    }
  };

  // --- GENERATE STORY HANDLERS ---

  const handleGenerateA = async () => {
    if (!spinA) return setError("Spin the wheel for Persona A first.");
    try {
      setError("");
      setLoadingA(true);
      const body = {
        persona: spinA.persona,
        context: spinA.context,
        language: "english",
        word_count: 600,
      };
      const data = await callJson(`${API_BASE}/api/generate-scenario`, {
        method: "POST",
        body: JSON.stringify(body),
      });
      setScenarioA(data.scenario);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoadingA(false);
    }
  };

  const handleGenerateB = async () => {
    if (!spinB) return setError("Spin the wheel for Persona B first.");
    try {
      setError("");
      setLoadingB(true);
      const body = {
        persona: spinB.persona,
        context: spinB.context,
        language: "english",
        word_count: 600,
      };
      const data = await callJson(`${API_BASE}/api/generate-scenario`, {
        method: "POST",
        body: JSON.stringify(body),
      });
      setScenarioB(data.scenario);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoadingB(false);
    }
  };

  // --- COMPARE TWO STORIES ---

  const handleCompare = async () => {
    if (!scenarioA || !scenarioB)
      return setError("Generate both scenarios before comparing.");

    try {
      setError("");
      setLoadingCompare(true);
      const body = {
        persona_a: spinA.persona,
        context_a: spinA.context,
        scenario_a: scenarioA,
        persona_b: spinB.persona,
        context_b: spinB.context,
        scenario_b: scenarioB,
      };
      const data = await callJson(`${API_BASE}/api/compare`, {
        method: "POST",
        body: JSON.stringify(body),
      });
      setComparison(data.comparison);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoadingCompare(false);
    }
  };

  // --- UI HELPERS ---

  const renderPersonaCard = (label, spin, onSpin, onGenerate, loading, story) => (
    <div
      style={{
        border: "1px solid #ddd",
        borderRadius: 8,
        padding: 16,
        width: "48%",
      }}
    >
      <h2>{label}</h2>

      <button onClick={onSpin} style={{ marginRight: 8 }}>
        Spin the wheel
      </button>
      <button onClick={onGenerate} disabled={!spin || loading}>
        {loading ? "Generating..." : "Generate story"}
      </button>

      {spin && (
        <div style={{ marginTop: 16, fontSize: 14 }}>
          <h3>Attributes</h3>
          <p><strong>Gender:</strong> {spin.persona.gender_identity}</p>
          <p><strong>Class:</strong> {spin.persona.social_class}</p>
          <p><strong>Occupation:</strong> {spin.persona.occupation}</p>
          <p><strong>Region:</strong> {spin.context.region}</p>
          <p><strong>Country:</strong> {spin.context.country_or_area}</p>
          <p>
            <strong>Period:</strong> {spin.context.year_from}–{spin.context.year_to}
          </p>
          <p><strong>Setting:</strong> {spin.context.urban_or_rural}</p>
        </div>
      )}

      {story && (
        <div
          style={{
            marginTop: 16,
            border: "1px solid #ccc",
            padding: 12,
            borderRadius: 6,
            whiteSpace: "pre-wrap",
            maxHeight: 250,
            overflowY: "auto",
          }}
        >
          {story}
        </div>
      )}
    </div>
  );

  // --- RENDER MAIN UI ---

  return (
    <div style={{ padding: 20, maxWidth: 1200, margin: "0 auto" }}>
      <h1>Spin-the-Wheel: Gendered Lives Across History</h1>
      <p>
        Spin the wheel to generate two personas from different places and times.  
        Generate their stories, then compare how gender, norms, and environment shaped their lives.
      </p>

      {error && <p style={{ color: "red" }}>Error: {error}</p>}

      {/* Two persona columns */}
      <div style={{ display: "flex", justifyContent: "space-between", marginTop: 20 }}>
        {renderPersonaCard(
          "Persona A",
          spinA,
          handleSpinA,
          handleGenerateA,
          loadingA,
          scenarioA
        )}
        {renderPersonaCard(
          "Persona B",
          spinB,
          handleSpinB,
          handleGenerateB,
          loadingB,
          scenarioB
        )}
      </div>

      {/* Compare button */}
      <div style={{ marginTop: 30 }}>
        <h2>Compare the two lives</h2>
        <button onClick={handleCompare} disabled={loadingCompare}>
          {loadingCompare ? "Comparing..." : "Compare A & B"}
        </button>

        {comparison && (
          <div
            style={{
              marginTop: 20,
              padding: 15,
              border: "1px solid #bbb",
              borderRadius: 6,
              background: "#f5f5ff",
              whiteSpace: "pre-wrap",
            }}
          >
            {comparison}
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
