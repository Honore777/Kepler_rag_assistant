import { configureStore, createSlice, PayloadAction } from '@reduxjs/toolkit'

type AuthState = {
  token: string | null
  user: string | null
}

const authSlice = createSlice({
  name: 'auth',
  initialState: { token: null, user: null } as AuthState,
  reducers: {
    setCredentials(state, action: PayloadAction<{ token: string; user: string | null }>) {
      state.token = action.payload.token
      state.user = action.payload.user
    },
    clearCredentials(state) {
      state.token = null
      state.user = null
    },
  },
})

export const { setCredentials, clearCredentials } = authSlice.actions

const store = configureStore({
  reducer: {
    auth: authSlice.reducer,
  },
})

export type RootState = ReturnType<typeof store.getState>
export type AppDispatch = typeof store.dispatch
export default store
