"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { saveUser } from "../../lib/auth";

export default function SupplierLogin() {
  const router = useRouter();

  const [mode, setMode] = useState<"login" | "register" | null>(null);
  const [phone, setPhone] = useState("");
  const [otp, setOtp] = useState(["", "", "", ""]);
  const [otpSent, setOtpSent] = useState(false);
  const [name, setName] = useState("");
  const [state, setState] = useState("");
  const [produce, setProduce] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const validatePhone = (p: string) => /^[6-9]\d{9}$/.test(p);

  const handleSendOtp = () => {
    setError("");
    if (!validatePhone(phone)) {
      setError("Please enter a valid 10-digit Indian mobile number");
      return;
    }
    setLoading(true);
    setTimeout(() => {
      setLoading(false);
      setOtpSent(true);
    }, 1000);
  };

  const handleOtpChange = (index: number, value: string) => {
    if (!/^\d*$/.test(value)) return;
    const newOtp = [...otp];
    newOtp[index] = value.slice(-1);
    setOtp(newOtp);
    if (value && index < 3) {
      const next = document.getElementById(`otp-${index + 1}`);
      next?.focus();
    }
  };

  const handleOtpKeyDown = (index: number, e: React.KeyboardEvent) => {
    if (e.key === "Backspace" && !otp[index] && index > 0) {
      const prev = document.getElementById(`otp-${index - 1}`);
      prev?.focus();
    }
  };

  const handleLogin = () => {
    setError("");
    const otpValue = otp.join("");
    if (otpValue.length !== 4) {
      setError("Please enter the 4-digit OTP");
      return;
    }
    if (otpValue !== "1234") {
      setError("Invalid OTP. Use 1234 for demo.");
      return;
    }
    saveUser({
      id: "V" + phone.slice(-4),
      name: "Supplier " + phone.slice(-4),
      phone,
      role: "vendor",
    });
    router.push("/chat");
  };

  const handleRegister = () => {
    setError("");
    if (!name.trim()) { setError("Please enter your name"); return; }
    if (!validatePhone(phone)) { setError("Please enter a valid 10-digit mobile number"); return; }
    if (!state.trim()) { setError("Please enter your state"); return; }
    if (!produce.trim()) { setError("Please enter type of produce"); return; }
    saveUser({
      id: "V" + phone.slice(-4),
      name,
      phone,
      role: "vendor",
    });
    router.push("/chat");
  };

  return (
    <div className="min-h-screen bg-black flex items-center justify-center text-white">
      <div className="w-full max-w-md bg-neutral-900 p-8 rounded-xl shadow-lg">

        <h2 className="text-2xl font-bold text-green-400 mb-2">Supplier Access</h2>
        <p className="text-sm text-gray-400 mb-6">Login or register as a supplier</p>

        {/* ERROR */}
        {error && (
          <div className="mb-4 px-4 py-2 bg-red-900/50 border border-red-700 rounded text-red-300 text-sm">
            ⚠ {error}
          </div>
        )}

        {/* MODE SELECTION */}
        {!mode && (
          <div className="space-y-4">
            <button onClick={() => setMode("login")}
              className="w-full py-3 rounded bg-green-700 hover:bg-green-600 transition">
              Existing Supplier → Login
            </button>
            <button onClick={() => setMode("register")}
              className="w-full py-3 rounded bg-green-600 hover:bg-green-500 transition">
              New Supplier → Register
            </button>
          </div>
        )}

        {/* LOGIN FORM */}
        {mode === "login" && (
          <>
            {!otpSent ? (
              <>
                <label className="block text-sm mt-4 mb-1">Mobile Number</label>
                <input
                  value={phone}
                  onChange={(e) => setPhone(e.target.value.replace(/\D/g, "").slice(0, 10))}
                  placeholder="10-digit mobile number"
                  className="w-full mb-4 px-4 py-3 rounded bg-neutral-800 border border-neutral-700 focus:outline-none focus:border-green-500"
                />
                <button
                  onClick={handleSendOtp}
                  disabled={loading}
                  className="w-full py-3 rounded bg-green-600 hover:bg-green-500 disabled:opacity-50 transition font-semibold"
                >
                  {loading ? "Sending OTP..." : "Send OTP"}
                </button>
              </>
            ) : (
              <>
                <p className="text-sm text-gray-400 mt-4 mb-3">
                  OTP sent to <span className="text-green-400">+91 {phone}</span>
                  <br/>
                  <span className="text-xs text-gray-500">(Use 1234 for demo)</span>
                </p>

                {/* OTP BOXES */}
                <div className="flex gap-3 justify-center mb-4">
                  {otp.map((digit, i) => (
                    <input
                      key={i}
                      id={`otp-${i}`}
                      value={digit}
                      onChange={(e) => handleOtpChange(i, e.target.value)}
                      onKeyDown={(e) => handleOtpKeyDown(i, e)}
                      maxLength={1}
                      className="w-14 h-14 text-center text-2xl font-bold rounded-lg bg-neutral-800 border-2 border-neutral-700 focus:border-green-500 focus:outline-none transition"
                    />
                  ))}
                </div>

                <button
                  onClick={handleLogin}
                  className="w-full py-3 rounded bg-green-600 hover:bg-green-500 transition font-semibold"
                >
                  Verify & Login
                </button>

                <button
                  onClick={() => { setOtpSent(false); setOtp(["", "", "", ""]); }}
                  className="w-full mt-3 text-xs text-gray-400 hover:text-white"
                >
                  ← Change Number
                </button>
              </>
            )}

            <button onClick={() => { setMode(null); setError(""); setOtpSent(false); setPhone(""); setOtp(["","","",""]); }}
              className="w-full mt-3 text-xs text-gray-400 hover:text-white">
              ← Back
            </button>
          </>
        )}

        {/* REGISTER FORM */}
        {mode === "register" && (
          <>
            <input value={name} onChange={(e) => setName(e.target.value)}
              placeholder="Supplier Name"
              className="w-full mb-3 px-4 py-3 rounded bg-neutral-800 border border-neutral-700 focus:outline-none focus:border-green-500 mt-4" />
            <input value={phone} onChange={(e) => setPhone(e.target.value.replace(/\D/g, "").slice(0, 10))}
              placeholder="Mobile Number"
              className="w-full mb-3 px-4 py-3 rounded bg-neutral-800 border border-neutral-700 focus:outline-none focus:border-green-500" />
            <input value={state} onChange={(e) => setState(e.target.value)}
              placeholder="State"
              className="w-full mb-3 px-4 py-3 rounded bg-neutral-800 border border-neutral-700 focus:outline-none focus:border-green-500" />
            <input value={produce} onChange={(e) => setProduce(e.target.value)}
              placeholder="Type of Produce"
              className="w-full mb-4 px-4 py-3 rounded bg-neutral-800 border border-neutral-700 focus:outline-none focus:border-green-500" />
            <button onClick={handleRegister}
              className="w-full py-3 rounded bg-green-600 hover:bg-green-500 transition font-semibold">
              Register & Continue
            </button>
            <button onClick={() => { setMode(null); setError(""); }}
              className="w-full mt-3 text-xs text-gray-400 hover:text-white">
              ← Back
            </button>
          </>
        )}
      </div>
    </div>
  );
}
