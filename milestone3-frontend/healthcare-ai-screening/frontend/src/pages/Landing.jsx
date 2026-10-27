import { Link } from 'react-router-dom'
import { Brain, LineChart, ScanLine, ShieldCheck } from 'lucide-react'
import { Disclaimer } from '../components/UI'
import { useAuth } from '../hooks/useAuth'

const features = [
  { icon: Brain, title: 'Disease-specific models', text: 'Separate, tested machine-learning models for breast cancer, diabetes and heart disease, compared against baselines.' },
  { icon: ShieldCheck, title: 'Explainable results', text: 'Every structured-data result lists the inputs that pushed the score up or down (SHAP).' },
  { icon: ScanLine, title: 'Image screening', text: 'Transfer-learning image classifier with Grad-CAM attention maps. Available once an image model has been trained on the server.' },
  { icon: LineChart, title: 'History and trends', text: 'Every screening you run is stored in your account so you can review it and see trends on the dashboard.' },
]

export default function Landing() {
  const { user } = useAuth()
  return (
    <div className="space-y-10">
      <section className="rounded-2xl bg-gradient-to-br from-brand-900 to-brand-600 p-8 text-white sm:p-12">
        <p className="text-sm font-semibold uppercase tracking-wide text-brand-100">Academic research prototype</p>
        <h1 className="mt-2 text-3xl font-bold sm:text-4xl">AI-Powered Multi-Disease Screening and Risk Assessment System</h1>
        <p className="mt-3 max-w-2xl text-brand-100">
          An explainable AI-based screening and clinical decision-support platform. It estimates screening scores, shows
          why, and keeps a history. It supports screening demonstrations; it does not diagnose.
        </p>
        <div className="mt-6 flex flex-wrap gap-3">
          {user ? (
            <Link to="/screen" className="btn bg-white text-brand-900 hover:bg-brand-50">Start a screening</Link>
          ) : (
            <>
              <Link to="/register" className="btn bg-white text-brand-900 hover:bg-brand-50">Create an account</Link>
              <Link to="/login" className="btn border border-white/60 text-white hover:bg-white/10">Sign in</Link>
            </>
          )}
          <Link to="/metrics" className="btn border border-white/60 text-white hover:bg-white/10">See model performance</Link>
        </div>
      </section>

      <section aria-label="Features" className="grid gap-4 sm:grid-cols-2">
        {features.map(({ icon: Icon, title, text }) => (
          <div key={title} className="card flex gap-4">
            <Icon className="h-8 w-8 shrink-0 text-brand-600" aria-hidden="true" />
            <div><h2 className="font-semibold">{title}</h2><p className="mt-1 text-sm text-slate-600">{text}</p></div>
          </div>
        ))}
      </section>

      <Disclaimer />
      <p className="text-center text-sm text-slate-600">
        Built with public, de-identified research datasets only. Please do not enter real patient information.{' '}
        <Link to="/about" className="font-medium text-brand-700 underline">Read the methodology and limitations</Link>.
      </p>
    </div>
  )
}
