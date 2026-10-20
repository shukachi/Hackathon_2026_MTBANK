import { useState } from "react";
import { useNavigate } from "react-router-dom";
import AppShell from "../../components/layout/AppShell";
import ChooseAgeStep from "./ChooseAgeStep";
import ConsentStep from "./ConsentStep";
import IssueCardStep from "./IssueCardStep";
import * as familiesApi from "../../api/families";
import { useFamily } from "../../context/FamilyContext";
import type { OnboardingResult } from "../../types";

export default function OnboardingWizard() {
  const navigate = useNavigate();
  const { addChild } = useFamily();
  const [step, setStep] = useState(1);
  const [childName, setChildName] = useState("");
  const [age, setAge] = useState("");
  const [consent, setConsent] = useState(false);
  const [ageError, setAgeError] = useState<string | null>(null);
  const [issuing, setIssuing] = useState(false);
  const [issueError, setIssueError] = useState<string | null>(null);
  const [result, setResult] = useState<OnboardingResult | null>(null);

  const handleAgeNext = () => {
    const ageNum = Number(age);
    if (!childName.trim()) {
      setAgeError("Укажите имя ребёнка");
      return;
    }
    if (!ageNum || ageNum < 7 || ageNum > 17) {
      setAgeError("Возраст должен быть от 7 до 17 лет");
      return;
    }
    setAgeError(null);
    setStep(2);
  };

  const handleIssue = async () => {
    setIssuing(true);
    setIssueError(null);
    try {
      const res = await familiesApi.onboardChild({
        child_full_name: childName,
        age: Number(age),
        consent_given: true,
      });
      setResult(res);
      addChild({ user: res.user, card: res.card });
    } catch (e) {
      setIssueError(e instanceof Error ? e.message : "Не удалось выпустить карту");
    } finally {
      setIssuing(false);
    }
  };

  const steps = [1, 2, 3];

  return (
    <AppShell>
      <div className="card" style={{ maxWidth: 480, margin: "0 auto", width: "100%" }}>
        <div className="step-indicator">
          {steps.map((s) => (
            <div key={s} className={`step-dot ${s === step ? "active" : s < step ? "done" : ""}`} />
          ))}
        </div>
        {step === 1 && (
          <ChooseAgeStep
            childName={childName}
            age={age}
            onChildNameChange={setChildName}
            onAgeChange={setAge}
            onNext={handleAgeNext}
            error={ageError}
          />
        )}
        {step === 2 && (
          <ConsentStep
            childName={childName}
            consent={consent}
            onConsentChange={setConsent}
            onBack={() => setStep(1)}
            onNext={() => setStep(3)}
          />
        )}
        {step === 3 && (
          <IssueCardStep
            childName={childName}
            age={age}
            onBack={() => setStep(2)}
            onIssue={handleIssue}
            issuing={issuing}
            error={issueError}
            result={result}
            onFinish={() => navigate("/parent", { replace: true })}
          />
        )}
      </div>
    </AppShell>
  );
}
