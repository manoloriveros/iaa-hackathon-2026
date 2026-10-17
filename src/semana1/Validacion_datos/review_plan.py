"""Alcance de revisión: estados de evidencia, pendientes y criterios explícitos de cierre."""


def plan():
    rows = []
    def add(code, area, priority, status, title, known, work, close, columns='*'):
        rows.append(dict(id=code, area=area, priority=priority, status=status, title=title,
                         known=known, remaining_work=work, closure_criterion=close, columns=columns.split()))
    add('VD01','Integridad','P0','verificado_con_alcance','Originales, versiones y catálogo',
        'D32/D36/D38 verifican originales, bitácoras y reversión; la auditoría actual comprueba hashes de entradas.',
        'Mantener el contrato de lectura por catálogo y comprobar sus hashes en cada ejecución relevante.',
        'Cada salida identifica versión, hash y reglas efectivas; los archivos de origen y corridas anteriores se conservan.')
    add('VD02','Integridad','P1','verificado_con_alcance','Esquemas, perfiles y dominios básicos',
        'D38 tiene 375 controles, 358 estrictos sin fallo; perfila 242 ocurrencias de columna y 105 nombres.',
        'Completar coherencia entre campos y fechas; un rango válido no certifica disponibilidad ni significado.',
        'Cada columna tiene ficha, nulos admisibles, tipo, dominio, unidad y prueba de coherencia pertinente.')
    add('VD03','Relaciones','P0','parcial','Cardinalidad de todas las uniones',
        'Maestros únicos y cruces de claves completos; ID01 restaura ceros iniciales en autos.',
        'Exigir many_to_one/one_to_one en la construcción real de X, verificar filas antes/después y conciliación de exposición y coste.',
        'Ningún join aumenta filas o importes salvo una expansión declarada; el clima se une por dirección y año.',
        'row_id policy_id customer_id address_id claim_id year')
    add('VD04','Siniestros','P0','hallazgo_nuevo','Duplicados con identificadores distintos',
        '604 pares tienen todos los campos iguales salvo claim_id; 1.208 filas implicadas. La unicidad del ID no detectaba esto.',
        'Revisar causas, congelar grupos, separar aceptados/rechazados y dentro/fuera de historia; decidir tratamiento sin borrar originales.',
        'Cohorte exacta y decisión justificada; comparación de conteos/coste antes y después; conservar ambas versiones si persiste incertidumbre.',
        'claim_id policy_id line peril loss_date report_date status paid_to_date incurred_to_date recoveries repairer_id third_party_id')
    add('VD05','Objetivo','P0','parcial','Asignación temporal de cada siniestro',
        'D38 encuentra asignación única o 414 anteriores al primer periodo: 297 motor, 67 edificios y 50 contenidos.',
        'Integrar esa lógica al constructor operativo y probar fronteras inclusivas, endosos, cancelaciones y filas sin siniestros.',
        'Cada claim_id tiene una categoría excluyente; cero ambigüedades y conciliación completa de conteos e importes.',
        'claim_id row_id policy_id line loss_date report_date period_start period_end')
    add('VD06','Objetivo','P0','pendiente_implementacion','Materializar T0 y sus componentes',
        'La fórmula está definida; existen proxies descriptivas, no una tabla operativa certificada sobre la versión vigente.',
        'Construir coste neto observado, pagos, recuperaciones, reserva, aceptados, positivos y abiertos por row_id; resolver primero VD04.',
        'Una fila por periodo, sin siniestros aceptados=0; sumas iguales al libro de siniestros incluido y exclusiones conciliadas.',
        'row_id claim_id status paid_to_date incurred_to_date recoveries exposure')
    add('VD07','Siniestros','P0','verificado_con_alcance','Dominio financiero y estados',
        'D38/D35: sin incurridos menores que pagos ni netos aceptados negativos; cerrados igualan pago/incurrido; un aceptado tiene coste neto cero.',
        'Conservar el caso cero y automatizar los controles dentro de T0; revisar recuperación bruta/neta y no restar franquicia dos veces.',
        'C-R y C-P conciliados; estado rechazado separado; cualquier excepción conserva su efecto monetario sin recorte silencioso.',
        'status paid_to_date incurred_to_date recoveries voluntary_excess compulsory_excess')
    add('VD08','Siniestros','P1','parcial','Datos ausentes de reparador y tercero',
        'Hay perfiles de faltantes; parte puede ser estructural por ramo y peligro.',
        'Cruzar presencia por ramo, peligro, estado y recuperaciones; no convertir ausencia en ausencia económica de tercero o reparación.',
        'Matriz de aplicabilidad documentada, excepciones revisadas y exclusión como predictor del mismo siniestro futuro.',
        'repairer_id third_party_id line peril recoveries')
    add('VD09','Coberturas','P0','hallazgo_nuevo','Cobertura de autos frente a peligro pagado',
        'El cruce nuevo encuentra cuatro aceptados de own_damage fuera de comprehensive: tres TPFT y uno TPO.',
        'Revisar las cuatro historias y póliza exacta por fecha; aclarar alcance contractual y posible error de producto o clasificación.',
        'Correspondencia producto/peligro documentada. No eliminar pagos ni imponer ceros de cobertura antes de resolverlo.',
        'cover_type peril line loss_date policy_id row_id')
    add('VD10','Coberturas','P0','hallazgo_nuevo','Daño accidental y cobertura opcional de hogar',
        'Hay 506 aceptados de edificios y 1.090 de contenidos con peril accidental_damage y bandera de cobertura falsa.',
        'Determinar si el código incluye cobertura básica, excepciones o errores; revisar la fila vigente a la ocurrencia.',
        'Regla de aplicabilidad respaldada; los 1.596 casos conservan coste hasta una decisión explícita.',
        'accidental_damage_cover peril line loss_date policy_id')
    add('VD11','Coberturas','P1','hallazgo_nuevo','Siniestros superiores al capital',
        'Se observan ocho aceptados de edificios y tres de contenidos cuyo neto incurrido supera el capital derivado de su periodo.',
        'Revisar por siniestro y no solo suma anual: límites, gastos, indexación, escala y tratamiento de recuperaciones.',
        'Cada caso tiene explicación o tratamiento versionado; no aplicar min(coste,capital) automáticamente.',
        'sum_insured incurred_to_date recoveries peril')
    add('VD12','Objetivo','P0','no_identificable_totalmente','Desarrollo de abiertos',
        'Solo hay una valoración a 31-12-2024; faltan snapshots financieros y fecha de cierre.',
        'Medir peso de reservas por ramo/peligro/cohorte y ejecutar sensibilidades T1; declarar que no hay verdad última observada.',
        'T0 reproducible y sensibilidad material documentada. No reconstruir triángulos de pagos ni afirmar validación del último sin datos adicionales.',
        'paid_to_date incurred_to_date status loss_date')
    add('VD13','Objetivo','P0','pendiente_implementacion','Siniestros no reportados y truncamiento',
        'El fichero omite siniestros no reportados al corte; los retrasos recientes están truncados.',
        'Validar conteos posteriores en cortes artificiales; contrastar completitud por peligro y su relación con severidad antes de T2.',
        'El ajuste se aprende dentro del corte, controla factores extremos y no corrige dos veces exposición/coste; límites de identificación explícitos.',
        'loss_date report_date peril line exposure')
    add('VD14','Objetivo','P1','parcial','Recuperaciones futuras',
        'T0 resta recuperaciones observadas una vez; no hay evolución histórica de recuperaciones.',
        'Revisar concentración por peligro y estado; mantener sensibilidad separada de reservas.',
        'No se supone que una recuperación observada nula en abierto sea una recuperación última nula.',
        'recoveries paid_to_date incurred_to_date status peril')
    add('VD15','Calendario','P0','verificado_con_alcance','Exposición aritmética y unidad de salida',
        'EXP01 coincide con días inclusivos/365 a cuatro decimales; es convención respaldada por datos, sin confirmación de organizador.',
        'Verificar exposición al transformar a tasa/importe, offset y frecuencia-severidad; declarar duración final conocida del periodo del concurso.',
        'La salida final es CU por periodo y la exposición se aplica exactamente una vez; no recortar por superar uno en un año bisiesto.',
        'period_start period_end exposure prediction')
    add('VD16','Calendario','P0','hallazgo_nuevo','Día omitido en la transición de 2024 a 2025',
        '500.245 continuidades dejan un día entre 30-12-2024 y 01-01-2025; no hay periodos que incluyan el 31-12-2024 ni siniestros en esa fecha.',
        'Confirmar convención del generador/calendario; revisar el efecto en exposición, ventana de ocurrencia e interpretación anual.',
        'Supuesto documentado y sensibilidad si procede; no extender fechas ni inventar siniestros o cobertura sin respaldo.',
        'period_start period_end exposure loss_date year')
    add('VD17','Calendario','P1','parcial','Endosos, cancelaciones y renovaciones',
        'No hay solapes y new_business coincide con renewal_count=0; la duración puede ser parcial.',
        'Revisar secuencia de renewal_count, decisión final, cambios intranuales y coherencia de las fechas con covariables y primas.',
        'Historias completas con cambios legítimos separados de saltos de registro; report_date fuera de cobertura no se confunde con loss_date fuera.',
        'new_business renewal_count renewal_decision policy_id period_start period_end written_premium')
    add('VD18','Disponibilidad','P0','pendiente_implementacion','Contrato de información por predictor',
        'F0–F4 están definidos en prosa/JSON; falta la matriz operativa con controles de corte y exclusión.',
        'Registrar fuente, instante de observación, ventana, rol permitido, supuesto y prueba de no acceso al futuro por columna.',
        'Cada predictor tiene disponibilidad justificada o queda fuera de F0; contrato aplicado por código, no solo escrito.')
    add('VD19','Disponibilidad','P0','abierto_semantico','Maestro de clientes sin fecha de versión',
        'Un registro por cliente, sin snapshots por año; nacimiento se adopta como referencia de AGE01.',
        'Distinguir nacimiento de variables cambiantes: ocupación, estado civil, crédito, hogar, puntos, dirección y marketing.',
        'Supuestos de estabilidad explícitos o exclusión/ablación por bloque; ninguna copia actual se presenta como dato histórico confirmado.',
        'date_of_birth occupation marital_status credit_band household_size licence_points years_at_address marketing_segment branch_id')
    add('VD20','Disponibilidad','P1','abierto_semantico','Maestro de inmuebles sin versiones',
        'No hay inmuebles construidos después del año de póliza en la revisión D38.',
        'Revisar estabilidad asumida de zona de inundación, energía, paneles, árboles, sótano, techo y habitaciones.',
        'Campos estables o fechados identificados; no usar una mejora posterior como conocida en una póliza anterior.',
        'flood_zone energy_rating solar_panels trees_within_5m basement roof_type bedrooms year_built listed_building property_type')
    add('VD21','Disponibilidad','P0','abierto_semantico','Clima anual futuro y publicación',
        'La tabla tiene todas las direcciones y años 2021–2025; completitud técnica no prueba disponibilidad al predecir.',
        'Excluir clima realizado de 2025 del escenario prospectivo; documentar publicación y usar solo historia disponible, con fallback para años sin pasado.',
        'Prueba que max(fecha disponible)<=corte en cada fold; ningún promedio o imputación incorpora años posteriores.',
        'address_id year hail_days wind_exposure_index freezing_days dry_summer_index wildfire_index rainfall_mm mean_temperature_c')
    add('VD22','Disponibilidad','P0','abierto_semantico','Telemática y ventanas de conducción',
        'La ausencia del score coincide con no optar por telemática, sin contradicciones de aplicabilidad.',
        'Aclarar cuándo se obtuvo el score y qué periodo resume; comparar bloque separado si no hay información previa.',
        'No usar conducción del mismo periodo para una predicción previa; ausente no equivale a puntuación cero.',
        'telematics_opt_in telematics_score')
    add('VD23','Disponibilidad','P0','abierto_semantico','Contactos, impagos y desocupación',
        'Son campos numéricamente válidos, pero no está fechado su anclaje temporal.',
        'Aclarar si contactos, impagos y máximo de desocupación se midieron antes de inicio o durante el periodo.',
        'Campos de cierre fuera del modelo prospectivo; los dudosos quedan en bloque separado con hipótesis declarada.',
        'customer_service_contacts missed_payments_12m days_unoccupied')
    add('VD24','Disponibilidad','P0','parcial','Renovación y etiquetas del periodo',
        'renewal_decision solo existe en entrenamiento y el protocolo lo excluye.',
        'Hacer cumplir por código la lista de exclusión: renovación final, costes, estados, periles del propio siniestro y columnas de auditoría.',
        'El constructor de X falla si recibe etiquetas o diagnósticos; entrenamiento y test tienen la misma lista de predictores.',
        'renewal_decision status peril incurred_to_date paid_to_date recoveries prediction')
    add('VD25','Disponibilidad','P1','abierto_semantico','Tarifa comercial y descuento',
        'written_premium es la prima del tarifario existente, no coste último. Hay perfiles, sin base anual/prorrateada confirmada.',
        'Aclarar unidad y momento de prima/descuento, endosos, devolución por cancelación y cargo total frente a periodo; analizar F4 aparte.',
        'Ninguna anualización automática ni cociente de siniestralidad con prima de base desconocida; comparar modelo sin tarifario.',
        'written_premium discount_applied channel payment_method days_quote_to_inception')
    add('VD26','Particiones','P0','pendiente_implementacion','Guardar V22/V23/V24 y roles',
        'El protocolo define años y hash para calibración/selección; todavía no hay particiones persistentes operativas.',
        'Guardar row_id, split, rol, corte, valoración y versión de etiqueta; comprobar exclusión entre roles y reproducibilidad.',
        'Manifiestos de filas y hashes exactos; nadie entrena/calibra/elige usando el holdout de evaluación.',
        'row_id policy_id customer_id address_id period_start')
    add('VD27','Particiones','P0','parcial','Dependencia entre personas, inmuebles y ramos',
        'D35 describe entidades conocidas/nuevas por ramo; no hay auditoría completa de componentes entre ramos y hogares.',
        'Medir clientes compartidos, direcciones compartidas y componentes conexas antes de dividir calibración/selección o remuestrear.',
        'Renovaciones temporales conservadas cuando reproducen el reto; dependencia declarada y estimación de incertidumbre por grupos.',
        'customer_id address_id policy_id row_id')
    add('VD28','Particiones','P0','no_identificable_totalmente','Valoración posterior en backtests históricos',
        'Todos los costes/estados se valoran en diciembre de 2024; no puede reconstruirse exactamente lo conocido en 2021–2023.',
        'Acotar las conclusiones de V22/V23/V24 como validación temporal proxy; evitar historia monetaria y filtros por estado final como disponibles antes.',
        'Cada resultado declara la valoración posterior; las carencias no se ocultan bajo una etiqueta de backtest causal.',
        'status paid_to_date incurred_to_date recoveries report_date loss_date')
    add('VD29','Particiones','P0','pendiente_implementacion','Preparación aprendida dentro de cada corte',
        'Hay reglas retrospectivas CAP01/AGE01/CAT01 y candidata CON01; no existe aún pipeline de folds que las controle.',
        'Congelar versiones y distinguir reparación de fuente, mapa retrospectivo y transformación estimada; entrenar imputadores/encoders solo con train.',
        'No se usan etiquetas de validación/test ni estadísticas futuras para limpiar, elegir categorías, escalar o completar valores.')
    add('VD30','Capitales','P1','abierto_semantico','Los 1.454 capitales pendientes',
        'Se preservan 593/98 edificios train/test y 671/92 contenidos; 879 con apoyo posterior, 467 contexto, 108 sin referencia normal.',
        'Revisar historias, unidad, endosos y dirección; separar propuesta causal de apoyo retrospectivo. No expandir CAP01 por cascada.',
        'Cada fila conserva justificación y decisión; sensibilidad al tratamiento y ninguna corrección por coste o score.',
        'sum_insured policy_id address_id construction_type occupancy tenure security_level')
    add('VD31','Construcción','P1','candidato_sin_activar','T/W como alias y nombre físico',
        'D39 respalda t,w→tw_code con 18.218 continuidades y cero contradicciones; candidata aislada, material sin confirmar.',
        'Resolver adopción en capa activa y fuente para el nombre físico; preservar literal y limitar la disponibilidad histórica del mapa.',
        'Versión efectiva inequívoca y comparación literal/armonizada; no declarar timber confirmado ni usar ambos como predictores redundantes.',
        'construction_type')
    add('VD32','Edades','P1','verificado_con_alcance','Edad del tomador y prioridad del nacimiento',
        'AGE01 corrigió 2.936 discrepancias de un año con referencia explícita al maestro; calendario y reversión verificados.',
        'Mantener el supuesto de fuente y convención de cumpleaños bisiesto; detectar nacimientos o roles nuevos en semana 2.',
        'La edad coincide con la fecha de inicio sin confundir conductor y tomador; discrepancias nuevas se investigan.',
        'date_of_birth policyholder_age driver_age period_start')
    add('VD33','Autos','P1','abierto_semantico','NCB frente a licencia e historial',
        '161.822 filas tienen NCB mayor que años de licencia (127.041 train, 34.781 test).',
        'Revisar duración acreditada, protección/traslado de bono, roles y progresión por renovación; no igualar ambos campos por defecto.',
        'Definición o regla justificada; sensibilidad literal/franjas/exclusión y sin aplicar min(NCB,licencia) por inferencia.',
        'ncb_years years_licensed driver_age prior_claims_5y')
    add('VD34','Autos','P1','hallazgo_nuevo','Edad implícita al obtener licencia',
        '3.717 filas dan driver_age-years_licensed<16; 16 es cribado analítico, no mínimo legal de un país supuesto.',
        'Revisar rol, redondeo, progresión y casos más extremos. No corregir con DOB del tomador sin identificar al conductor.',
        'Casos explicados o limitación explícita; no declarar ilegalidad ni imponer una edad mínima universal.',
        'driver_age years_licensed customer_id')
    add('VD35','Autos','P1','hallazgo_nuevo','Cilindrada de eléctricos',
        '99.376 filas electric: 96.843 con engine_size_cc positivo y 2.533 ausentes; todos los valores informados son positivos.',
        'Aclarar si es cilindrada física, grupo equivalente o error del generador; comparar tratamiento por combustible en una variable derivada.',
        'Unidad y aplicabilidad documentadas; no convertir automáticamente todo eléctrico a cero ni atribuir al dato una mecánica inexistente.',
        'engine_size_cc fuel_type make_model body_type transmission vehicle_value_group')
    add('VD36','Autos','P1','pendiente_revision','Continuidad de conductor y vehículo',
        'policy_id es continuo, pero no hay driver_id ni vehicle_id; un endoso puede cambiar de objeto.',
        'Comparar edad, antigüedad de licencia/vehículo, make_model y atributos dentro de cada historia; separar cambio de vehículo y salto de registro.',
        'No se fuerza incremento anual o inmutabilidad cuando cambió la persona/vehículo; firmas parciales documentadas.',
        'policy_id driver_age years_licensed vehicle_age make_model engine_size_cc fuel_type body_type transmission seats vehicle_colour driver_assist')
    add('VD37','Autos','P1','pendiente_revision','Kilometraje, uso y conductores adicionales',
        'Hay dominios y no negatividad, sin interpretación completa de exposición anual y fecha de declaración.',
        'Revisar colas, ceros, annual_mileage anual frente a periodo parcial, uso comercial y named_young_driver frente al conductor principal.',
        'No prorratear dos veces kilometraje ni corregir conductor joven basándose solo en edad del principal.',
        'annual_mileage vehicle_use named_young_driver driver_age overnight_parking')
    add('VD38','Hogar','P1','pendiente_revision','Características físicas y ocupación',
        'Existen perfiles y dominios válidos; no toda combinación válida está contrastada.',
        'Examinar tipo de propiedad, techo, antigüedad, habitaciones, sótano, ocupación, tenure, hipoteca y señal de protección con contexto.',
        'Las combinaciones raras son casos de revisión, no reglas universales para borrar filas; los cruces entre edificios/contenidos respetan personas y dirección.',
        'year_built property_type roof_type bedrooms basement listed_building occupancy tenure mortgage smoke_alarms security_level high_value_items works_from_home lodgers bicycle_cover')
    add('VD39','Hogar','P1','pendiente_revision','Inundación, río, elevación y geología',
        'Zonas 1–5 válidas, distancias no negativas y perfiles disponibles; sin coordenadas ni mapas externos del territorio ficticio.',
        'Revisar combinaciones de zona/distancia/elevación/suelo y faltantes; no inferir que toda relación debe ser monótona.',
        'Casos extremos revisados y soporte por región; elevación negativa relativa al río no se elimina automáticamente.',
        'flood_zone distance_to_river_km elevation_m soil_type region urban_density')
    add('VD40','Clima','P1','parcial','Coherencia física y temporal del clima',
        'Unicidad dirección/año y cinco años completos verificadas, con dominios de índices y no negatividad.',
        'Comprobar días frente a 365/366, colas, coherencia entre índices y medidas, persistencia regional y cambios de unidad por año.',
        'Reglas físicas justificadas sin aplicar relaciones deterministas inventadas; fecha de disponibilidad resuelta por VD21.',
        'hail_days freezing_days wind_exposure_index rainfall_mm dry_summer_index wildfire_index mean_temperature_c year')
    add('VD41','Faltantes','P1','parcial','Ausencia estructural, de captura y temporal',
        'Perfiles de todas las columnas y aplicabilidad telemática verificados; no se ha imputado nada.',
        'Cruzar máscaras de nulos por año, ramo, producto, dirección y endoso; medir coausencias y estabilidad entre train/test.',
        'Ausente, no aplica y cero se separan; no se declara MCAR por observar un 2,5% aproximadamente.',
        'telematics_score occupation credit_band flood_zone smoke_alarms days_unoccupied engine_size_cc roof_type soil_type energy_rating campaign_code repairer_id third_party_id')
    add('VD42','Faltantes','P0','pendiente_implementacion','Imputadores y desconocidos de producción',
        'La capa derivada conserva nulos y no tiene una estrategia de entrenamiento implementada.',
        'Definir por modelo tratamiento de nulos, categoría desconocida, columna totalmente ausente y fallback de segmentos nuevos.',
        'Ajuste solo con train del fold; prueba de categoría nueva/null y mismo transformador en predicción; sin ffill a través de cambios de riesgo.')
    add('VD43','Distribución','P1','parcial','Deriva por año en la capa vigente',
        'D30 comparó 73 campos de pólizas train/test; sus cifras de exposición, construcción y edad son anteriores a correcciones.',
        'Recalcular solo estadísticas afectadas y ampliar a maestros, coberturas y nulos; separar mezcla de composición y unidad.',
        'Informe por año/ramo con soporte, exposición y entidades nuevas; sin llamar error a toda diferencia ni usar un umbral PSI universal.')
    add('VD44','Distribución','P1','pendiente_revision','Soporte, colas y segmentos nuevos',
        'Hay perfiles marginales; no una ficha completa de soporte de interacciones futuras.',
        'Medir celdas raras/nuevas por ramo, producto, edad, capital, región y combustible; distinguir filas de clientes independientes.',
        'Decisión de agrupar/shrinkage/fallback aprendida en entrenamiento; sin extrapolación tarifaria presentada como evidencia suficiente.',
        'region cover_type make_model fuel_type policyholder_age driver_age sum_insured construction_type')
    add('VD45','Distribución','P1','pendiente_revision','Concentración de coste y eventos comunes',
        'Hay agregados por peligro, sin estudio completo de concentración y eventos compartidos.',
        'Medir contribución de mayores siniestros, top clientes/direcciones y fechas-regiones para tormenta/inundación.',
        'Sensibilidad documentada sin winsorizar o eliminar severos válidos; incertidumbre no basada solo en independencia por fila.',
        'peril loss_date region address_id incurred_to_date recoveries')
    add('VD46','Inflación','P1','no_identificable_totalmente','Tendencia monetaria frente a desarrollo y mezcla',
        'Un solo corte de reservas mezcla inflación, exposición, cobertura, maduración y composición.',
        'Separar tendencias de capital/prima/coste y cohortes maduras; comparar hipótesis a 2025 sin doble inflación.',
        'Toda proyección económica declara supuestos; no se estima inflación como simple pendiente del incurrido anual.',
        'sum_insured written_premium incurred_to_date paid_to_date exposure loss_date period_start')
    add('VD47','Historia','P0','pendiente_implementacion','Historial de siniestros conocido al corte',
        'prior_claims_5y es declaración antes de ingresar; no es conteo móvil de los siniestros proporcionados.',
        'Si se añaden conteos históricos, exigir ocurrencia y reporte conocidos; no filtrar por rechazo/cierre final desconocido.',
        'Prueba de no acceso al futuro y separación por persona/póliza; importes históricos desactivados si no hay snapshots.',
        'prior_claims_5y loss_date report_date status policy_id customer_id')
    add('VD48','Relaciones','P1','pendiente_revision','Señal multirramo y hogares',
        'Los maestros permiten clientes multirramo y personas que comparten dirección.',
        'Auditar conflictos de tenure/ocupación o características y señales trasladadas entre ramos; permitir varios hogares/roles legítimos.',
        'No sumar dos veces siniestros ni copiar etiquetas retenidas de otro ramo; toda predicción intermedia es generada fuera de muestra.',
        'customer_id address_id occupancy tenure household_size policyholder_age')
    add('VD49','Identidad','P1','parcial','Memorización y artefactos de identificadores',
        'Los IDs son texto y no se usan como predictores iniciales; filas globalmente únicas en el sondeo actual.',
        'Revisar patrones de orden/longitud y duplicados semánticos; excluir nombres y no usar apellido/DOB para fusionar personas.',
        'Las relaciones usan claves; cualquier experimento con ID queda separado y no se presenta como relatividad causal de riesgo.',
        'row_id policy_id customer_id address_id claim_id surname date_of_birth email_domain')
    add('VD50','Métrica','P0','pendiente_implementacion','Unidad monetaria y scorer efectivo',
        'Potencia Tweedie 1,5 y cálculo en CU por periodo definidos; el scorer oficial completo no está verificado.',
        'Verificar implementación real, escala, pesos provisionales, ceros, positividad, agregación global y por ramo.',
        'La misma fórmula puntúa candidatos sobre las mismas filas/etiqueta; no confundir D² en tasa con D² en importe.',
        'prediction exposure incurred_to_date recoveries row_id')
    add('VD51','Entrega','P0','parcial','Cobertura de filas y orden final',
        'Los 626.639 IDs de test coinciden una vez con la plantilla; no existe una entrega real de modelos.',
        'Ensamblar por row_id, comprobar una predicción por fila, esquema, finitud, dominio, orden requerido y ausencia de índices extra.',
        'Archivo final exacto identificado por hash; columnas de sample_submission nunca se usan como verdad de entrenamiento.',
        'row_id prediction')
    add('VD52','Operación','P1','pendiente_implementacion','Contrato de datos para la segunda semana',
        'Se anunció nuevo dataset y retos; su contrato concreto no está disponible.',
        'Preparar validaciones de esquema, unidades, códigos nuevos, cambios de objetivo y ventanas antes de aplicar reglas de esta semana.',
        'El flujo falla de forma explícita ante cambios relevantes y produce cola de revisión; CAP01 no se extrapola a otra cohorte.')
    add('VD53','Trazabilidad','P0','parcial','Reglas activas frente a propuestas',
        'D38 es la capa activa; CON01 está verificada como candidata sin activar.',
        'Registrar una sola versión efectiva, lista de exclusiones y estado de cada decisión; evitar que un script lea un reporte histórico como certificación vigente.',
        'Catálogo/configuración/modelo apuntan al mismo snapshot y cada transformación es trazable hasta el dato original.')
    add('VD54','Revisión','P1','no_realizado','Reproducción y revisión independiente',
        'Los controles existentes son propios asistidos por IA; otro algoritmo no constituye revisor independiente.',
        'Reconstruir desde instrucciones/snapshots y obtener revisión competente independiente si existe disponibilidad y autorización compatible.',
        'Afirmar solo el nivel realmente alcanzado; la falta de revisor no se sustituye por dos llamadas a la misma IA.')
    add('VD55','Uso profesional','P1','pendiente_revision','Proxies y justificación tarifaria',
        'Crédito, ocupación y marketing pueden ser predictivos pero requieren propósito y contexto; el territorio es ficticio.',
        'Comparar soporte y estabilidad por segmentos, variables comerciales frente a riesgo y usos permitidos; evitar conclusiones normativas sin jurisdicción.',
        'Selección justificada y límites declarados; correlación/SHAP no se convierten en causalidad ni justificación automática de trato tarifario.',
        'credit_band occupation marital_status marketing_segment branch_id email_domain surname vehicle_colour region')
    add('VD56','Clientes','P1','pendiente_revision','Antigüedad, hogar y datos de adquisición',
        'D38 no encuentra adquisición posterior al año de póliza; no confirma el anclaje del resto del maestro.',
        'Comparar years_at_address con edad y mudanzas bajo una fecha explícita; customer_since_year con antigüedad/renovaciones; distinguir previo a ingreso de ventana móvil.',
        'Reglas de coherencia con año parcial y roles, sin transformar una diferencia de definición en error automático.',
        'years_at_address customer_since_year date_of_birth household_size prior_claims_5y previous_insurer campaign_code renewal_count new_business')
    add('VD57','Comercial','P1','pendiente_revision','Canales y atributos de relación',
        'Dominios de canal/pago/preferencia válidos; campañas y sucursales carecen de fecha histórica.',
        'Revisar cambios de canal, pagos, consentimiento, segmento, proveedor y preferencias; separar captura, marketing y selección comercial de riesgo técnico.',
        'No interpretar campaña ausente como campaña cero ni usar decisiones posteriores para explicar siniestralidad anterior.',
        'channel payment_method marketing_consent marketing_segment campaign_code branch_id document_preference previous_insurer email_domain days_quote_to_inception')
    add('VD58','Revisión','P0','pendiente_implementacion','Criterio para empezar y criterio para entregar',
        'No se ha aprobado una base final para modelar; algunos límites no son resolubles con estos archivos.',
        'Cerrar bloqueos de integridad/objetivo y acotar incertidumbres con exclusiones/sensibilidades; permitir piloto T0 con alcance declarado.',
        'Lista de aceptación por etapa: piloto T0, comparación, candidato 2025 y entrega. No exigir identificar perfectamente el último para iniciar una referencia.')
    return rows
