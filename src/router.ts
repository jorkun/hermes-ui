import { createRouter, createWebHistory } from 'vue-router'
import ChatPage from '@/pages/ChatPage.vue'
import SettingsPage from '@/pages/SettingsPage.vue'
import SessionsPage from '@/pages/SessionsPage.vue'
import MemoryPage from '@/pages/MemoryPage.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/chat' },
    { path: '/chat', component: ChatPage, meta: { title: '聊天' } },
    { path: '/settings', component: SettingsPage, meta: { title: '设置' } },
    { path: '/sessions', component: SessionsPage, meta: { title: '会话' } },
    { path: '/memory', component: MemoryPage, meta: { title: '记忆' } },
  ],
})

export default router
