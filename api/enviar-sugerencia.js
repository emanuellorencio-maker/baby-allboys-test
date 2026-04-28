module.exports = async function handler(req, res) {
  if (req.method !== "POST") {
    res.setHeader("Allow", "POST");
    return res.status(405).json({ ok: false, error: "Metodo no permitido" });
  }

  try {
    const { nombre = "", mensaje = "", zonaActual = "", vistaActual = "", fechaHora = "" } = req.body || {};
    const texto = String(mensaje || "").trim();

    if (!texto) {
      return res.status(400).json({ ok: false, error: "Mensaje obligatorio" });
    }

    const apiKey = process.env.RESEND_API_KEY;
    const destino = process.env.SUGERENCIAS_EMAIL;

    const payload = {
      from: "Baby All Boys <onboarding@resend.dev>",
      to: [destino],
      subject: "Sugerencia Baby All Boys",
      text: [
        "Nueva sugerencia desde Baby All Boys",
        "",
        `Nombre: ${String(nombre || "Sin nombre").trim()}`,
        `Zona: ${String(zonaActual || "-").trim()}`,
        `Vista: ${String(vistaActual || "-").trim()}`,
        `Fecha/hora: ${String(fechaHora || "-").trim()}`,
        "",
        "Mensaje:",
        texto,
      ].join("\n"),
    };

    if (!apiKey || !destino) {
      console.warn("enviar-sugerencia: faltan RESEND_API_KEY o SUGERENCIAS_EMAIL");
      return res.status(200).json({ ok: true, delivered: false });
    }

    const respuesta = await fetch("https://api.resend.com/emails", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${apiKey}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });

    if (!respuesta.ok) {
      const detalle = await respuesta.text().catch(() => "");
      console.error("enviar-sugerencia: Resend fallo", respuesta.status, detalle);
      return res.status(200).json({ ok: true, delivered: false });
    }

    return res.status(200).json({ ok: true, delivered: true });
  } catch (error) {
    console.error("enviar-sugerencia: error interno", error);
    return res.status(200).json({ ok: true, delivered: false });
  }
};
