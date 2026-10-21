import { useEffect, useState } from "react";
import QRCode from "qrcode";

interface QrCodeProps {
  /** Строка, которую нужно закодировать (например `moby://pay/<token>`). */
  value: string;
  size?: number;
}

/**
 * Отрисовка QR-кода.
 *
 * Используем пакет `qrcode` — он не тянёт canvas/dom в рантайм и рисует SVG,
 * поэтому код остаётся резким на любом экране и не ломается в headless-окружении.
 */
export default function QrCode({ value, size = 220 }: QrCodeProps) {
  const [svg, setSvg] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    QRCode.toString(value, {
      type: "svg",
      margin: 1,
      width: size,
      errorCorrectionLevel: "M",
      color: { dark: "#14213d", light: "#ffffff" },
    })
      .then((res) => {
        if (!cancelled) {
          setSvg(res);
          setError(null);
        }
      })
      .catch(() => {
        if (!cancelled) setError("Не удалось построить QR-код");
      });
    return () => {
      cancelled = true;
    };
  }, [value, size]);

  if (error) return <div className="alert alert-error">{error}</div>;
  if (!svg) return <div className="muted">Строим QR-код...</div>;

  return (
    <div
      className="qr-canvas"
      // SVG приходит из нашей же библиотеки, внешние данные туда не попадают.
      dangerouslySetInnerHTML={{ __html: svg }}
    />
  );
}
