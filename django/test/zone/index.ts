import instance from '@/api/instance1'

export const apiGetTableData = (url: string, query: any = null) => {
  return instance.request({ method: 'get', url, params: query })
}
export const apiGetTableSchema = (pageName: string) => {
  return instance.request({ method: 'get', url: '/main/schema', params: { pageName } })
}
export const refreshZone = () => {
  return instance.request({ method: 'get', url: '/zone/refresh', timeout: 20000 })
}
export const apiEditTableData = (url: string, data: any) => {
  return instance.request({ method: 'put', url, data })
}
export const apiCreateTableData = (url: string, data: any) => {
  return instance.request({ method: 'post', url, data })
}
