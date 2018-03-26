# Proxecto EMEEHL


Aspectos xerais do Proxecto de Medición para a Eficiencia Enerxética en Hardware Libre (emeehl)

Co proxecto EMEEHL trátase de deseñar e construír dous equipos didácticos de medición necesarios para a avaliación da eficiencia enerxética en edificios e industrias. Estes equipos construiranse empregando hardware e software libre e porase á disposición da comunidade as especificaciòns e diagramas de funcionamento. O público destinatario destes equipos é os profesores e alumnos das familias profesionais de 'Enerxía e Auga' e 'Instalación e Mantemento?, dos Ciclos de Formación Profesional.

Os equipos comerciais existentes no mercado teñen un alto prezo que dificulta a compra e uso dos mesmos por parte de centros educativos con poucos recursos. Neste proxecto preténdese poñer á disposición da comunidade educativa instrumentos de medición totalmente funcionais que se podan construir de xeito sinxelo e con baixo custe.

Os equipos que se desenvolverán na fase inicial son:

Equipo de medición portátil de transmitancia térmica Equipo de medición contínua de parámetros de confort e eficiencia enerxética das aulas (temperatura, humidade, calidade do aire, luminosidade, ruído, etc).


# Termofluxómetro
O termofluxómetro ou medidor portátil de transmitancia térmica é un equipo de medición continua que a partir dos datos de temperatura ambiente interior e exterior e temperatura superficial de parede interior, é capaz de dar unha medida da facilidade (conductividade) coa que un fluxo de calor é capaz de atravesar un cerramento. Este equipo dispón de tres elementos: (a) sensor exterior, (b) sensor interior e (c) receptor e procesador de valores. Os dous primeiros elementos consisten en sendos módulos ESP8266 conectados a sondas de temperatura (DS18b20), que emiten periodicamente os valores lidos ao receptor central. Este último unha Raspberry Pi programada para escoitar aos sensores, realizar os cálculos e publicar os resultados tanto periodica como asincronamente.
Neste repositorio publícanse os scripts correspondentes aos sensores exterior e interior, así como o da Raspberry.

