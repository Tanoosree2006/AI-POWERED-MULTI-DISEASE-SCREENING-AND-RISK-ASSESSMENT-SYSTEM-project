import { api } from '../services/api'
import { useAsync } from '../hooks/useAsync'
import { Disclaimer, PageTitle } from '../components/UI'

export default function About() {
  const { data } = useAsync(() => api.diseases().catch(() => []), [])
  return (
    <div className="space-y-6">
      <PageTitle title="About, methodology and limitations" subtitle="AI-Powered Multi-Disease Screening and Risk Assessment System (Aditya University, CSE, 2026-27)" />
      <Disclaimer />
      <section className="card">
        <h2 className="text-lg font-semibold">Module status on this server</h2>
        <ul className="mt-2 space-y-1 text-sm">
          {(data || []).map((d) => <li key={d.id}><strong>{d.name}</strong>: {d.status === 'available' ? 'available' : 'not available (model not trained)'}</li>)}
          {(!data || data.length === 0) && <li className="text-slate-500">Status could not be loaded.</li>}
        </ul>
      </section>
      <section className="card space-y-2 text-sm text-slate-700">
        <h2 className="text-lg font-semibold text-slate-900">Methodology</h2>
        <p>Each tabular module uses a stratified 60/20/20 train/validation/test split. Imputation and scaling live inside the model pipeline and are fitted on training data only. Logistic Regression, Random Forest and XGBoost are tuned by 5-fold cross-validation on the training set; the best model is selected on the validation set; the test set is used once. SHAP explains tabular predictions; Grad-CAM visualises where an image model focused.</p>
        <p>The image module uses transfer learning (an ImageNet-pretrained ResNet fine-tuned on a public dataset). It is only available when a trained model has been installed.</p>
      </section>
      <section className="card space-y-2 text-sm text-slate-700">
        <h2 className="text-lg font-semibold text-slate-900">Datasets</h2>
        <ul className="list-disc pl-6">
          <li>Breast cancer: UCI Breast Cancer Wisconsin (Diagnostic), 569 samples, CC BY 4.0.</li>
          <li>Diabetes: Pima Indians Diabetes Database (NIDDK), 768 rows, all female patients of Pima heritage aged 21+.</li>
          <li>Heart disease: UCI Heart Disease, Cleveland subset, 302 rows after removing one duplicate.</li>
        </ul>
      </section>
      <section className="card space-y-2 text-sm text-slate-700">
        <h2 className="text-lg font-semibold text-slate-900">Limitations</h2>
        <ul className="list-disc pl-6">
          <li>Small, single-source datasets: results are optimistic and may not transfer to other populations. No external validation has been done.</li>
          <li>Scores are uncalibrated model outputs, not probabilities. A lower score does not exclude disease.</li>
          <li>SHAP and Grad-CAM describe model behaviour, not medical causes. Correlated inputs share credit; heat maps can highlight artefacts.</li>
          <li>The diabetes dataset represents one population; missing values (recorded as zeros) are filled with training medians.</li>
          <li>Some categorical codes in the heart dataset are inconsistently documented publicly.</li>
          <li>The system has not been clinically validated, is not regulated as a medical device, and has no hospital integration.</li>
        </ul>
      </section>
      <section className="card space-y-2 text-sm text-slate-700">
        <h2 className="text-lg font-semibold text-slate-900">Privacy and data handling</h2>
        <p>Use public research data only. Your account stores the numeric inputs, score and explanation of each screening so you can review them; you can delete any record from the History page. Uploaded images are analysed in memory and are never stored; only a hash fingerprint and the score are kept. Passwords are stored hashed. Do not enter real patient information.</p>
      </section>
    </div>
  )
}
