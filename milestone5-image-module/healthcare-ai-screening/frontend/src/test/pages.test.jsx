import { beforeEach, describe, expect, it, vi } from 'vitest'
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'

vi.mock('../services/api', () => {
  const api = { me: vi.fn(), login: vi.fn(), register: vi.fn(), diseases: vi.fn(), examples: vi.fn(), screen: vi.fn(),
    screenImage: vi.fn(), history: vi.fn(), record: vi.fn(), deleteRecord: vi.fn(), dashboard: vi.fn(), metrics: vi.fn() }
  let token = null
  return { api, tokenStore: { get: () => token, set: (t) => { token = t }, clear: () => { token = null } } }
})

import { api, tokenStore } from '../services/api'
import { ApiError } from '../services/apiClient'
import AppRoutes from '../App'
import { AuthProvider } from '../hooks/useAuth'

const renderAt = (path) => render(<MemoryRouter initialEntries={[path]}><AuthProvider><AppRoutes /></AuthProvider></MemoryRouter>)
const signIn = (role = 'user') => { tokenStore.set('tok'); api.me.mockResolvedValue({ id: 1, username: 'alice', role }) }

const DISEASES = [
  { id: 'diabetes', name: 'Diabetes risk screening', description: 'desc', data_type: 'tabular', status: 'available', dataset: 'Pima', n_features: 3, model: 'random_forest',
    features: [
      { name: 'age', label: 'Age', kind: 'number', min: 18, max: 100, unit: 'years', help: '', allowed: null, nullable: false },
      { name: 'glucose', label: 'Plasma glucose', kind: 'number', min: 30, max: 400, unit: 'mg/dL', help: 'Leave blank if unknown.', allowed: null, nullable: true },
      { name: 'sex', label: 'Sex', kind: 'binary', min: 0, max: 1, unit: '', help: '0 = female, 1 = male', allowed: [0, 1], nullable: false }] },
  { id: 'heart_disease', name: 'Heart disease screening', description: 'd', data_type: 'tabular', status: 'unavailable' },
  { id: 'image_screening', name: 'Image screening', description: 'd', data_type: 'image', status: 'unavailable' },
]
const RECORD = { id: 5, disease: 'breast_cancer', model: 'logistic_regression', model_version: 'v1', screening_score: 0.8742, threshold: 0.5, screening_flag: 'elevated',
  warnings: ["'mean radius'=500 outside training range [7, 28]; prediction may be unreliable"], disclaimer: 'x', created_at: '2026-10-12T10:00:00',
  explanation: { unit: 'log-odds', base_value: -0.5, caveat: 'SHAP shows how the model used each input.', top_features: [
    { feature: 'radius error', value: 1.2, shap: 2.36, effect: 'raises score' }, { feature: 'worst texture', value: 20.1, shap: -0.9, effect: 'lowers score' }] } }

beforeEach(() => { vi.resetAllMocks(); tokenStore.clear(); window.confirm = vi.fn(() => true) })

describe('public pages', () => {
  it('landing page states the prototype status and does not overclaim', () => {
    renderAt('/')
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent(/Multi-Disease Screening/)
    expect(screen.getAllByText(/not a medical device/i).length).toBeGreaterThan(0)
    expect(screen.getByText(/not been clinically validated/i)).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /create an account/i })).toBeInTheDocument()
    expect(document.body.textContent).not.toMatch(/FDA|approved|hospital integration achieved/i)
  })
  it('about page lists live module status and limitations', async () => {
    api.diseases.mockResolvedValue(DISEASES)
    renderAt('/about')
    expect(await screen.findByText(/Diabetes risk screening/)).toBeInTheDocument()
    expect(screen.getByText(/Image screening/)).toBeInTheDocument()
    expect(screen.getAllByText(/not available/i).length).toBeGreaterThan(0)
    expect(screen.getByRole('heading', { name: 'Limitations' })).toBeInTheDocument()
  })
  it('unknown routes show a not-found page', () => { renderAt('/nope'); expect(screen.getByText(/page not found/i)).toBeInTheDocument() })
})

describe('authentication', () => {
  it('redirects signed-out users from protected pages to sign in', async () => {
    renderAt('/history')
    expect(await screen.findByRole('heading', { name: 'Sign in' })).toBeInTheDocument()
    expect(api.history).not.toHaveBeenCalled()
  })
  it('validates the sign-in form before calling the server', async () => {
    renderAt('/login')
    await userEvent.click(screen.getByRole('button', { name: /sign in/i }))
    expect(await screen.findByText(/at least 3 characters/i)).toBeInTheDocument()
    expect(screen.getByText(/password is required/i)).toBeInTheDocument()
    expect(api.login).not.toHaveBeenCalled()
  })
  it('signs in, stores the token and lands on the dashboard', async () => {
    api.login.mockResolvedValue({ access_token: 'tok123' }); api.me.mockResolvedValue({ id: 1, username: 'alice', role: 'user' })
    api.dashboard.mockResolvedValue({ total_screenings: 0 })
    renderAt('/login')
    await userEvent.type(screen.getByLabelText('Username'), 'alice'); await userEvent.type(screen.getByLabelText('Password'), 'correct-horse-1')
    await userEvent.click(screen.getByRole('button', { name: /^sign in$/i }))
    expect(await screen.findByText(/no screenings yet/i)).toBeInTheDocument()
    expect(api.login).toHaveBeenCalledWith('alice', 'correct-horse-1'); expect(tokenStore.get()).toBe('tok123')
    expect(screen.getByText(/signed in as/i)).toHaveTextContent('alice')
  })
  it('shows a server error on bad credentials', async () => {
    api.login.mockRejectedValue(new ApiError('Invalid username or password', 401))
    renderAt('/login')
    await userEvent.type(screen.getByLabelText('Username'), 'alice'); await userEvent.type(screen.getByLabelText('Password'), 'x')
    await userEvent.click(screen.getByRole('button', { name: /^sign in$/i }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Invalid username or password')
    expect(tokenStore.get()).toBeNull()
  })
  it('enforces the 8-character password rule when registering', async () => {
    renderAt('/register')
    await userEvent.type(screen.getByLabelText('Username'), 'newuser'); await userEvent.type(screen.getByLabelText('Password'), 'short')
    await userEvent.click(screen.getByRole('button', { name: /create account/i }))
    expect(await screen.findByText(/at least 8 characters/i)).toBeInTheDocument(); expect(api.register).not.toHaveBeenCalled()
  })
  it('signing out returns to the landing page', async () => {
    signIn(); api.dashboard.mockResolvedValue({ total_screenings: 0 })
    renderAt('/dashboard')
    await userEvent.click(await screen.findByRole('button', { name: /sign out/i }))
    expect(await screen.findByRole('link', { name: /create an account/i })).toBeInTheDocument(); expect(tokenStore.get()).toBeNull()
  })
})

describe('module selection and screening form', () => {
  it('lists modules and marks unavailable ones honestly', async () => {
    signIn(); api.diseases.mockResolvedValue(DISEASES)
    renderAt('/screen')
    expect(await screen.findByText('Diabetes risk screening')).toBeInTheDocument()
    expect(screen.getAllByRole('link', { name: /start screening/i })).toHaveLength(1)
    expect(screen.getAllByText(/not available: model not trained/i)).toHaveLength(2)
  })
  it('blocks submission with invalid values and explains each problem', async () => {
    signIn(); api.diseases.mockResolvedValue(DISEASES)
    renderAt('/screen/diabetes')
    await userEvent.click(await screen.findByRole('button', { name: /run screening/i }))
    expect(await screen.findByText(/please fix 2 problems/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/^Age/)).toHaveAttribute('aria-invalid', 'true')
    expect(api.screen).not.toHaveBeenCalled()
  })
  it('rejects out-of-range numbers', async () => {
    signIn(); api.diseases.mockResolvedValue(DISEASES)
    renderAt('/screen/diabetes')
    fireEvent.change(await screen.findByLabelText(/^Age/), { target: { value: '5' } })
    fireEvent.change(screen.getByLabelText(/Sex/), { target: { value: '1' } })
    await userEvent.click(screen.getByRole('button', { name: /run screening/i }))
    expect((await screen.findAllByText(/Age must be at least 18/)).length).toBeGreaterThanOrEqual(2) // summary + inline message
    expect(api.screen).not.toHaveBeenCalled()
  })
  it('sends numbers, uses null for blank optional fields, then opens the result', async () => {
    signIn(); api.diseases.mockResolvedValue(DISEASES); api.screen.mockResolvedValue({ id: 5 }); api.record.mockResolvedValue(RECORD)
    renderAt('/screen/diabetes')
    fireEvent.change(await screen.findByLabelText(/^Age/), { target: { value: '45' } })
    fireEvent.change(screen.getByLabelText(/Sex/), { target: { value: '1' } })
    expect(screen.getByLabelText(/Plasma glucose.*optional/)).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: /run screening/i }))
    await waitFor(() => expect(api.screen).toHaveBeenCalledWith('diabetes', { age: 45, glucose: null, sex: 1 }))
    expect(await screen.findByRole('heading', { name: /model-estimated screening score/i })).toBeInTheDocument()
  })
  it('fills a real dataset example when asked', async () => {
    signIn(); api.diseases.mockResolvedValue(DISEASES); api.examples.mockResolvedValue({ dataset_positive_example: { age: 61, glucose: null, sex: 1 }, dataset_negative_example: {} })
    renderAt('/screen/diabetes')
    await userEvent.click(await screen.findByRole('button', { name: /labelled positive in the dataset/i }))
    await waitFor(() => expect(screen.getByLabelText(/^Age/)).toHaveValue(61))
    expect(screen.getByLabelText(/Plasma glucose/)).toHaveValue(null)
  })
  it('shows server-side validation errors without losing the form', async () => {
    signIn(); api.diseases.mockResolvedValue(DISEASES); api.screen.mockRejectedValue(new ApiError("Feature 'age' must be at least 18", 422))
    renderAt('/screen/diabetes')
    fireEvent.change(await screen.findByLabelText(/^Age/), { target: { value: '45' } }); fireEvent.change(screen.getByLabelText(/Sex/), { target: { value: '0' } })
    await userEvent.click(screen.getByRole('button', { name: /run screening/i }))
    expect(await screen.findByText(/must be at least 18/)).toBeInTheDocument(); expect(screen.getByLabelText(/^Age/)).toHaveValue(45)
  })
  it('refuses to render an unavailable or unknown module', async () => {
    signIn(); api.diseases.mockResolvedValue(DISEASES)
    renderAt('/screen/heart_disease'); expect(await screen.findByText(/not available: its model has not been trained/i)).toBeInTheDocument()
  })
})

describe('result page', () => {
  it('presents the score as an uncalibrated model score with warnings, SHAP and the disclaimer', async () => {
    signIn(); api.record.mockResolvedValue(RECORD)
    renderAt('/results/5')
    expect(await screen.findByText('0.874')).toBeInTheDocument()
    expect(screen.getByText(/Elevated screening score/)).toBeInTheDocument()
    expect(screen.getByText(/not a probability of disease and not a diagnosis/i)).toBeInTheDocument()
    expect(screen.getByRole('alert')).toHaveTextContent(/outside training range/)
    const table = screen.getByRole('table', { name: /SHAP contributions/i })
    expect(within(table).getByText('radius error')).toBeInTheDocument(); expect(within(table).getByText('lowers score')).toBeInTheDocument()
    expect(screen.getByText(/not clinically validated/i)).toBeInTheDocument()
  })
  it('explains missing explanation data for image records', async () => {
    signIn(); api.record.mockResolvedValue({ ...RECORD, disease: 'image_screening', warnings: [], explanation: { method: 'grad-cam', note: 'Heat map is generated on request and is not stored.' } })
    renderAt('/results/5'); expect(await screen.findByText(/not stored/i)).toBeInTheDocument()
  })
  it('shows an error with retry when the record cannot be loaded', async () => {
    signIn(); api.record.mockRejectedValueOnce(new ApiError('Record not found', 404)).mockResolvedValueOnce(RECORD)
    renderAt('/results/9'); expect(await screen.findByRole('alert')).toHaveTextContent('Record not found')
    await userEvent.click(screen.getByRole('button', { name: /try again/i })); expect(await screen.findByText('0.874')).toBeInTheDocument()
  })
})

describe('history and dashboard', () => {
  const item = (id) => ({ id, user_id: 1, disease: 'diabetes', model: 'rf', model_version: 'v', screening_score: 0.4, screening_flag: 'lower', created_at: '2026-10-12T10:00:00' })
  it('renders rows and deletes a record after confirmation', async () => {
    signIn(); api.history.mockResolvedValue({ total: 2, limit: 10, offset: 0, items: [item(2), item(1)] }); api.deleteRecord.mockResolvedValue(true)
    renderAt('/history')
    expect(await screen.findByRole('table', { name: /screening history/i })).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: 'Delete record 2' }))
    expect(window.confirm).toHaveBeenCalled(); await waitFor(() => expect(api.deleteRecord).toHaveBeenCalledWith(2))
    await waitFor(() => expect(api.history).toHaveBeenCalledTimes(2))
  })
  it('does not delete when the user cancels', async () => {
    signIn(); window.confirm = vi.fn(() => false); api.history.mockResolvedValue({ total: 1, limit: 10, offset: 0, items: [item(1)] })
    renderAt('/history'); await userEvent.click(await screen.findByRole('button', { name: 'Delete record 1' }))
    expect(api.deleteRecord).not.toHaveBeenCalled()
  })
  it('shows an empty state and filters by module', async () => {
    signIn(); api.history.mockResolvedValue({ total: 0, limit: 10, offset: 0, items: [] })
    renderAt('/history'); expect(await screen.findByText(/no screenings found/i)).toBeInTheDocument()
    await userEvent.selectOptions(screen.getByLabelText(/filter by module/i), 'diabetes')
    await waitFor(() => expect(api.history).toHaveBeenLastCalledWith({ limit: 10, offset: 0, disease: 'diabetes' }))
  })
  it('only offers the all-users view to admins', async () => {
    signIn('user'); api.history.mockResolvedValue({ total: 0, limit: 10, offset: 0, items: [] })
    renderAt('/history'); await screen.findByText(/no screenings found/i); expect(screen.queryByLabelText(/all users/i)).toBeNull()
  })
  it('dashboard shows totals from the API, never sample data', async () => {
    signIn(); api.dashboard.mockResolvedValue({ scope: 'own', window_days: 90, total_screenings: 7, flagged_elevated: 3, flagged_lower: 4, mean_score: 0.4321,
      by_disease: { diabetes: 7 }, trend: [{ date: '2026-10-12', count: 7, flagged: 3, mean_score: 0.43 }], recent: [item(1)], note: 'Counts are model-flagged screening scores, not confirmed diagnoses.' })
    renderAt('/dashboard')
    expect(await screen.findByText('Total screenings')).toBeInTheDocument(); expect(screen.getByText('7', { selector: 'p' })).toBeInTheDocument()
    expect(screen.getByText('0.432')).toBeInTheDocument(); expect(screen.getByText(/not confirmed diagnoses/i)).toBeInTheDocument()
  })
})

describe('model performance page', () => {
  const m = (cm) => ({ selected_model: 'logistic_regression', split: { train: 60, val: 20, test: 20 }, threshold: 0.5,
    test: { logistic_regression: { accuracy: 0.9, precision: 0.8, recall_sensitivity: 0.75, specificity: 0.95, f1: 0.77, roc_auc: 0.93, brier_score: 0.1, ece_10bin: 0.05, confusion_matrix: cm },
            random_forest: { accuracy: 0.85, precision: 0.7, recall_sensitivity: 0.65, specificity: 0.9, f1: 0.7, roc_auc: 0.9, brier_score: 0.12, ece_10bin: 0.07, confusion_matrix: cm } },
    repeated_cv_train_plus_val: { logistic_regression: { roc_auc: { mean: 0.91, std: 0.03 }, recall: { mean: 0.7, std: 0.05 }, specificity: { mean: 0.9, std: 0.02 }, accuracy: { mean: 0.8, std: 0.02 } } },
    high_sensitivity_operating_point: { threshold: 0.24, chosen_on: 'validation set', test: { recall_sensitivity: 0.96, specificity: 0.55, confusion_matrix: { tn: 18, fp: 15, fn: 1, tp: 27 } } } })
  it('renders every number from the API response, with tabs and caveats', async () => {
    api.metrics.mockResolvedValue({ breast_cancer: m({ tn: 71, fp: 1, fn: 2, tp: 40 }), diabetes: m({ tn: 80, fp: 20, fn: 10, tp: 44 }) })
    renderAt('/metrics')
    expect(await screen.findByRole('heading', { name: /breast cancer: test-set results/i })).toBeInTheDocument()
    expect(screen.getByText('0.9300')).toBeInTheDocument(); expect(screen.getByText('71')).toBeInTheDocument()
    expect(screen.getByText(/42 positive cases/)).toBeInTheDocument(); expect(screen.getByText(/0\.910 ± 0\.030/)).toBeInTheDocument()
    expect(screen.getByText(/sensitivity 96\.0%/)).toBeInTheDocument(); expect(screen.getByText(/Small test sets make these numbers noisy/)).toBeInTheDocument()
    await userEvent.click(screen.getByRole('tab', { name: 'Diabetes' }))
    expect(await screen.findByRole('heading', { name: /diabetes: test-set results/i })).toBeInTheDocument()
  })
  it('shows an error when results are unavailable', async () => {
    api.metrics.mockRejectedValue(new ApiError('No evaluation results available. Run the training script.', 404))
    renderAt('/metrics'); expect(await screen.findByRole('alert')).toHaveTextContent(/No evaluation results/)
  })
})

describe('image screening page', () => {
  const IMG = { id: 'image_screening', name: 'Image screening', data_type: 'image', status: 'available', model: 'resnet18', positive_class: 'Parasitized' }
  beforeEach(() => { globalThis.URL.createObjectURL = vi.fn(() => 'blob:preview'); globalThis.URL.revokeObjectURL = vi.fn() })
  it('says plainly that the module is unavailable and offers no upload', async () => {
    signIn(); api.diseases.mockResolvedValue(DISEASES)
    renderAt('/image'); expect(await screen.findByText(/not available on this server/i)).toBeInTheDocument(); expect(screen.queryByLabelText(/choose a png/i)).toBeNull()
  })
  it('rejects unsupported files on the client', async () => {
    signIn(); api.diseases.mockResolvedValue([IMG]); const user = userEvent.setup({ applyAccept: false })
    renderAt('/image'); await user.upload(await screen.findByLabelText(/choose a png/i), new File(['x'], 'notes.txt', { type: 'text/plain' }))
    expect(await screen.findByText(/only png and jpeg/i)).toBeInTheDocument(); expect(screen.getByRole('button', { name: /analyse image/i })).toBeDisabled(); expect(api.screenImage).not.toHaveBeenCalled()
  })
  it('uploads a valid image and shows the score and the Grad-CAM caveat', async () => {
    signIn(); api.diseases.mockResolvedValue([IMG])
    api.screenImage.mockResolvedValue({ id: 3, screening_score: 0.71, threshold: 0.5, screening_flag: 'elevated',
      gradcam: { overlay_png_base64: 'AAAA', caveat: 'Grad-CAM shows where the model focused. It is not proof of disease.' } })
    renderAt('/image'); const file = new File(['png'], 'cell.png', { type: 'image/png' })
    await userEvent.upload(await screen.findByLabelText(/choose a png/i), file)
    await userEvent.click(screen.getByRole('button', { name: /analyse image/i }))
    expect(await screen.findByText('0.710')).toBeInTheDocument(); expect(api.screenImage).toHaveBeenCalledWith(file)
    expect(screen.getByAltText(/grad-cam heat map overlay/i)).toHaveAttribute('src', 'data:image/png;base64,AAAA'); expect(screen.getByText(/not proof of disease/i)).toBeInTheDocument()
  })
  it('shows server rejections of bad images', async () => {
    signIn(); api.diseases.mockResolvedValue([IMG]); api.screenImage.mockRejectedValue(new ApiError('File is not a valid PNG or JPEG image', 422))
    renderAt('/image'); await userEvent.upload(await screen.findByLabelText(/choose a png/i), new File(['x'], 'a.png', { type: 'image/png' }))
    await userEvent.click(screen.getByRole('button', { name: /analyse image/i })); expect(await screen.findByRole('alert')).toHaveTextContent(/not a valid/)
  })
})
