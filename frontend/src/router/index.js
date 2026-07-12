import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Login',
    component: () => import('../views/LoginView.vue'),
    meta: { guest: true }
  },
  {
    path: '/admin',
    name: 'AdminDashboard',
    component: () => import('../views/AdminDashboard.vue'),
    meta: { role: 'admin' }
  },
  {
    path: '/admin/tambah-penerbit',
    name: 'TambahPenerbit',
    component: () => import('../views/TambahPenerbit.vue'),
    meta: { role: 'admin' }
  },
  {
    path: '/admin/data-penerbit',
    name: 'DataPenerbit',
    component: () => import('../views/DataPenerbit.vue'),
    meta: { role: 'admin' }
  },
  {
    path: '/publisher',
    name: 'PublisherDashboard',
    component: () => import('../views/PublisherDashboard.vue'),
    meta: { role: 'penerbit' }
  },
  {
    path: '/publisher/terbitkan',
    name: 'TerbitkanSertifikat',
    component: () => import('../views/TerbitkanSertifikat.vue'),
    meta: { role: 'penerbit' }
  },
  {
    path: '/publisher/monitoring',
    name: 'MonitoringData',
    component: () => import('../views/MonitoringData.vue'),
    meta: { role: 'penerbit' }
  },
  {
    path: '/verifikasi/valid',
    name: 'VerifikasiValid',
    component: () => import('../views/VerifikasiValid.vue')
  },
  {
    path: '/verifikasi/invalid',
    name: 'VerifikasiInvalid',
    component: () => import('../views/VerifikasiInvalid.vue')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  const userStr = localStorage.getItem('user')
  let user = null
  if (userStr) {
    try {
      user = JSON.parse(userStr)
    } catch (e) {
      user = null
    }
  }

  // Jika halaman guest (login) dan sudah login, redirect ke dashboard
  if (to.meta.guest) {
    if (token && user) {
      if (user.role === 'admin') {
        next('/admin')
      } else if (user.role === 'penerbit') {
        next('/publisher')
      } else {
        next('/')
      }
    } else {
      next()
    }
    return
  }

  // Jika tidak ada token, redirect ke login
  if (!token) {
    next('/')
    return
  }

  // Jika ada role yang dibutuhkan dan user tidak punya role yang sesuai
  if (to.meta.role && user?.role !== to.meta.role) {
    // Redirect ke dashboard masing-masing
    if (user?.role === 'admin') {
      next('/admin')
    } else if (user?.role === 'penerbit') {
      next('/publisher')
    } else {
      next('/')
    }
    return
  }

  next()
})

export default router