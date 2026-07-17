import { createRouter, createWebHistory } from 'vue-router'
import LoginView from '../views/LoginView.vue'
import AdminDashboard from '../views/AdminDashboard.vue'
import PublisherDashboard from '../views/PublisherDashboard.vue'
import TambahPenerbit from '../views/TambahPenerbit.vue'
import DataPenerbit from '../views/DataPenerbit.vue'
import TerbitkanSertifikat from '../views/TerbitkanSertifikat.vue'
import MonitoringData from '../views/MonitoringData.vue'
import VerifikasiValid from '../views/VerifikasiValid.vue'
import VerifikasiInvalid from '../views/VerifikasiInvalid.vue'

const routes = [
  {
    path: '/',
    name: 'Login',
    component: LoginView,
    meta: { requiresAuth: false }
  },
  {
    path: '/admin',
    name: 'AdminDashboard',
    component: AdminDashboard,
    meta: { requiresAuth: true, role: 'admin' }
  },
  {
    path: '/publisher',
    name: 'PublisherDashboard',
    component: PublisherDashboard,
    meta: { requiresAuth: true, role: 'penerbit' }
  },
  {
    path: '/admin/tambah-penerbit',
    name: 'TambahPenerbit',
    component: TambahPenerbit,
    meta: { requiresAuth: true, role: 'admin' }
  },
  {
    path: '/admin/data-penerbit',
    name: 'DataPenerbit',
    component: DataPenerbit,
    meta: { requiresAuth: true, role: 'admin' }
  },
  {
    path: '/publisher/terbitkan',
    name: 'TerbitkanSertifikat',
    component: TerbitkanSertifikat,
    meta: { requiresAuth: true, role: 'penerbit' }
  },
  {
    path: '/publisher/monitoring',
    name: 'MonitoringData',
    component: MonitoringData,
    meta: { requiresAuth: true, role: 'penerbit' }
  },

  {
    path: '/verifikasi/valid',
    name: 'VerifikasiValid',
    component: VerifikasiValid,
    meta: { requiresAuth: false }
  },
  {
    path: '/verifikasi/invalid',
    name: 'VerifikasiInvalid',
    component: VerifikasiInvalid,
    meta: { requiresAuth: false }
  },
  // Redirect jika path tidak ditemukan
  {
    path: '/:pathMatch(.*)*',
    redirect: '/'
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// Navigation Guard (Cek Auth)
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  const user = JSON.parse(localStorage.getItem('user') || '{}')
  const requiresAuth = to.meta.requiresAuth
  const requiredRole = to.meta.role

  // Jika halaman membutuhkan auth tapi tidak ada token
  if (requiresAuth && !token) {
    next('/')
    return
  }

  // Jika halaman membutuhkan role tertentu
  if (requiresAuth && requiredRole && user.role !== requiredRole) {
    if (user.role === 'admin') {
      next('/admin')
    } else if (user.role === 'penerbit') {
      next('/publisher')
    } else {
      next('/')
    }
    return
  }

  // Jika sudah login dan mengakses halaman login, redirect ke dashboard sesuai role
  if (to.path === '/' && token) {
    if (user.role === 'admin') {
      next('/admin')
    } else if (user.role === 'penerbit') {
      next('/publisher')
    } else {
      next('/')
    }
    return
  }

  next()
})

export default router