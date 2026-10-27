/** Original image next to the Grad-CAM overlay, with the mandatory "attention, not proof" label. */
export default function GradCamView({ originalUrl, gradcam }) {
  if (!gradcam) return null
  return (
    <section aria-labelledby="gc-title" className="card">
      <h2 id="gc-title" className="text-lg font-semibold">Grad-CAM attention map</h2>
      <div className="mt-4 grid gap-4 sm:grid-cols-2">
        <figure>
          {originalUrl && <img src={originalUrl} alt="Uploaded image" className="w-full rounded-lg border" />}
          <figcaption className="mt-1 text-center text-xs text-slate-500">Uploaded image</figcaption>
        </figure>
        <figure>
          <img src={`data:image/png;base64,${gradcam.overlay_png_base64}`} alt="Grad-CAM heat map overlay" className="w-full rounded-lg border" />
          <figcaption className="mt-1 text-center text-xs text-slate-500">Warmer colours = regions the model weighted more</figcaption>
        </figure>
      </div>
      <p className="mt-3 rounded-md bg-slate-100 p-3 text-xs text-slate-700">{gradcam.caveat}</p>
    </section>
  )
}
