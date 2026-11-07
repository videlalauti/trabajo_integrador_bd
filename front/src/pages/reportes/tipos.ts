export interface TopVino {
  cod_vino: number
  vino: string
  tipo: string
  botellas_vendidas: number
}

export interface VentaPorSala {
  id_sala: number
  calle: string
  numero: string
  total_ventas: string | number
}

export interface VinoSinStock {
  cod_vino: number
  vino: string
  tipo: string
  anada: number
  volumen_ml: number
  stock_sala: number
  stock_deposito: number
}

export interface ListadoVinosSinStock {
  items: VinoSinStock[]
  total: number
  pagina: number
  tamanio: number
}

export interface Sala {
  id_sala: number
  calle: string
  numero: string
  localidad: string
}
