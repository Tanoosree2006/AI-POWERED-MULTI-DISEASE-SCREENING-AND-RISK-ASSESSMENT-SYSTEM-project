import { Link } from 'react-router-dom'
export default function NotFound() {
  return (<div className="card text-center"><h1 className="text-xl font-bold">Page not found</h1><p className="mt-2 text-sm text-slate-600">That page does not exist.</p><Link className="btn btn-primary mt-4" to="/">Go home</Link></div>)
}
