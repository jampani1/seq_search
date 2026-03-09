# Expressões Matemáticas para Organelas Celulares

## Objetivo
Estruturar funções matemáticas que descrevem formas orgânicas para visualização 3D de células vegetais.

---

## 1. Formas Base

### 1.1 Superelipsóide (Forma Universal)
A maioria das organelas pode ser descrita como variações de superelipsóides:

```
x = a * cos^n1(θ) * cos^n2(φ)
y = b * sin^n1(θ) * cos^n2(φ)
z = c * sin^n2(φ)

onde:
- a, b, c = semi-eixos (dimensões)
- n1, n2 = parâmetros de "squareness" (quanto maior, mais quadrado)
- θ ∈ [0, 2π], φ ∈ [-π/2, π/2]
```

| n1, n2 | Forma Resultante |
|--------|------------------|
| 1, 1   | Elipsóide perfeito |
| 0.5, 0.5 | Forma estrelada |
| 2, 2   | Cubo arredondado |
| 1, 0.5 | Forma de almofada |

---

## 2. Organelas Específicas

### 2.1 Núcleo (Envelope Nuclear)
**Forma**: Esfera com deformação por ruído

```javascript
// Esfera base com perturbação
radius(θ, φ) = R₀ + A * noise3D(
    sin(θ)*cos(φ),
    sin(θ)*sin(φ),
    cos(θ)
)

onde:
- R₀ = raio base (~5μm em escala real)
- A = amplitude do ruído (0.05-0.15 * R₀)
- noise3D = Perlin/Simplex noise
```

**Implementação Three.js**:
```javascript
function createNucleus(radius, detail) {
    const geometry = new THREE.IcosahedronGeometry(radius, detail);
    const positions = geometry.attributes.position;

    for (let i = 0; i < positions.count; i++) {
        const x = positions.getX(i);
        const y = positions.getY(i);
        const z = positions.getZ(i);

        const noise = simplex3D(x * 2, y * 2, z * 2) * 0.1;
        const length = Math.sqrt(x*x + y*y + z*z);
        const scale = 1 + noise;

        positions.setXYZ(i, x * scale, y * scale, z * scale);
    }
    geometry.computeVertexNormals();
    return geometry;
}
```

---

### 2.2 Mitocôndria
**Forma**: Cápsula alongada com cristae internas

```
// Superfície externa (cápsula)
Forma = Cilindro(r, h) ∪ Hemisfério_topo(r) ∪ Hemisfério_base(r)

// Cristae (dobras internas) - ondulações senoidais
z_crista(x, y) = A * sin(ω * x) * exp(-y²/σ²)

onde:
- r = raio (~0.5μm)
- h = comprimento (~2-4μm)
- A = amplitude das cristae (0.1-0.2 * r)
- ω = frequência (4-8 dobras por μm)
```

**Implementação**:
```javascript
function createMitochondria(length, radius) {
    const curve = new THREE.CatmullRomCurve3([
        new THREE.Vector3(-length/2, 0, 0),
        new THREE.Vector3(-length/4, 0.1, 0.05),  // leve curvatura
        new THREE.Vector3(0, 0, -0.05),
        new THREE.Vector3(length/4, -0.1, 0.03),
        new THREE.Vector3(length/2, 0, 0)
    ]);

    return new THREE.TubeGeometry(curve, 32, radius, 16, false);
}

// Cristae como planos ondulados internos
function createCristae(mitoLength, count) {
    const cristae = [];
    for (let i = 0; i < count; i++) {
        const x = -mitoLength/2 + (i + 1) * mitoLength / (count + 1);
        // Plano com deformação senoidal
        const plane = createWavyPlane(0.3, 0.4, 8);
        plane.position.x = x;
        plane.rotation.y = Math.PI/2;
        cristae.push(plane);
    }
    return cristae;
}
```

---

### 2.3 Cloroplasto
**Forma**: Elipsóide achatado (disco lenticular) com tilacóides

```
// Envelope externo - elipsóide oblato
x²/a² + y²/a² + z²/c² = 1    onde a > c (achatado em z)

// Granum (pilha de tilacóides) - cilindros empilhados
Granum = Σᵢ Cilindro(r_granum, h_disco, posição_i)

// Lamelas (conexões entre grana)
Lamela = TuboConector(granum_i, granum_j)
```

**Parâmetros típicos**:
```
a = 3-5μm (raio maior)
c = 1-2μm (espessura)
r_granum = 0.3-0.5μm
h_disco = 0.02μm por tilacóide
n_discos = 10-20 por granum
n_grana = 40-60 por cloroplasto
```

**Implementação**:
```javascript
function createChloroplast(a, c) {
    // Envelope - esfera achatada
    const envelope = new THREE.SphereGeometry(a, 32, 32);
    envelope.scale(1, 1, c/a);  // achatar em Z

    // Grana (pilhas de tilacóides)
    const grana = [];
    const granaCount = 8;

    for (let i = 0; i < granaCount; i++) {
        const angle = (i / granaCount) * Math.PI * 2;
        const r = a * 0.5;  // raio de distribuição

        const granum = createGranum(0.15, 10);
        granum.position.set(
            Math.cos(angle) * r,
            Math.sin(angle) * r,
            0
        );
        grana.push(granum);
    }

    return { envelope, grana };
}

function createGranum(radius, layers) {
    const group = new THREE.Group();
    const spacing = 0.02;

    for (let i = 0; i < layers; i++) {
        const disc = new THREE.CylinderGeometry(radius, radius, 0.01, 16);
        const mesh = new THREE.Mesh(disc, thylakoidMaterial);
        mesh.position.y = i * spacing - (layers * spacing / 2);
        group.add(mesh);
    }
    return group;
}
```

---

### 2.4 Retículo Endoplasmático (RE)
**Forma**: Rede de tubos e cisternas conectadas

```
// RE Rugoso - rede de tubos com ribossomos
Tubo_i = SplineCurve3D(pontos_controle_i, raio)
Ribossomo_j = Esfera(r_pequeno, posição_na_superfície)

// RE Liso - tubos mais lisos sem ribossomos
// Usar L-systems para gerar ramificações
```

**L-System para ramificação**:
```
Axioma: F
Regras:
    F → F[+F][-F]F

onde:
    F = avançar e desenhar tubo
    + = girar +30°
    - = girar -30°
    [ = salvar estado (push)
    ] = restaurar estado (pop)
```

**Implementação**:
```javascript
function createER(iterations, length, radius) {
    const tubes = [];
    const stack = [];
    let position = new THREE.Vector3(0, 0, 0);
    let direction = new THREE.Vector3(1, 0, 0);

    const commands = generateLSystem('F', iterations);

    for (const cmd of commands) {
        switch(cmd) {
            case 'F':
                const end = position.clone().add(
                    direction.clone().multiplyScalar(length)
                );
                tubes.push(createTube(position, end, radius));
                position = end;
                break;
            case '+':
                direction.applyAxisAngle(
                    new THREE.Vector3(0, 0, 1),
                    Math.PI/6
                );
                break;
            case '-':
                direction.applyAxisAngle(
                    new THREE.Vector3(0, 0, 1),
                    -Math.PI/6
                );
                break;
            case '[':
                stack.push({pos: position.clone(), dir: direction.clone()});
                break;
            case ']':
                const state = stack.pop();
                position = state.pos;
                direction = state.dir;
                break;
        }
    }
    return tubes;
}
```

---

### 2.5 Complexo de Golgi
**Forma**: Pilha de cisternas achatadas (dictiossomo)

```
// Cisterna individual - disco curvado
z(x, y) = A * (1 - (x/a)² - (y/b)²) * H(1 - x²/a² - y²/b²)

onde:
- A = curvatura máxima
- a, b = semi-eixos
- H = função Heaviside (limita ao interior da elipse)

// Pilha de cisternas
Golgi = Σᵢ Cisterna(z_offset = i * espaçamento)
```

**Características**:
- Face cis (entrada): cisternas mais convexas
- Face trans (saída): cisternas mais achatadas
- Vesículas de transporte entre cisternas

```javascript
function createGolgi(layers) {
    const group = new THREE.Group();
    const spacing = 0.08;

    for (let i = 0; i < layers; i++) {
        // Curvatura diminui da cis para trans
        const curvature = 0.3 - (i * 0.04);
        const cisterna = createCisterna(1.0, 0.5, curvature);
        cisterna.position.y = i * spacing;
        group.add(cisterna);

        // Vesículas entre camadas
        if (i < layers - 1) {
            const vesicles = createVesicles(3, 0.05);
            vesicles.position.y = i * spacing + spacing/2;
            group.add(vesicles);
        }
    }
    return group;
}

function createCisterna(width, depth, curvature) {
    const geometry = new THREE.PlaneGeometry(width, depth, 20, 10);
    const positions = geometry.attributes.position;

    for (let i = 0; i < positions.count; i++) {
        const x = positions.getX(i);
        const y = positions.getY(i);
        // Função de curvatura parabólica
        const z = curvature * (1 - 4*x*x/(width*width) - 4*y*y/(depth*depth));
        positions.setZ(i, Math.max(0, z));
    }

    geometry.computeVertexNormals();
    return new THREE.Mesh(geometry, cisternaMaterial);
}
```

---

### 2.6 Vacúolo Central
**Forma**: Grande esfera irregular (ocupa 80-90% da célula vegetal)

```
// Tonoplasto (membrana do vacúolo) - esfera com ruído
r(θ, φ) = R₀ * (1 + Σₙ Aₙ * Yₙₘ(θ, φ))

onde:
- R₀ = raio base
- Yₙₘ = harmônicos esféricos (para deformações suaves)
- Aₙ = amplitudes (pequenas, ~0.05-0.1)
```

```javascript
function createVacuole(radius, irregularity) {
    const geometry = new THREE.IcosahedronGeometry(radius, 4);
    const positions = geometry.attributes.position;

    for (let i = 0; i < positions.count; i++) {
        const x = positions.getX(i);
        const y = positions.getY(i);
        const z = positions.getZ(i);

        // Deformação suave usando múltiplas frequências
        const noise =
            0.5 * simplex3D(x, y, z) +
            0.25 * simplex3D(x*2, y*2, z*2) +
            0.125 * simplex3D(x*4, y*4, z*4);

        const scale = 1 + noise * irregularity;
        positions.setXYZ(i, x * scale, y * scale, z * scale);
    }

    geometry.computeVertexNormals();
    return geometry;
}
```

---

### 2.7 DNA (Dupla Hélice)
**Forma**: Duas espirais entrelaçadas com "degraus"

```
// Backbone (esqueleto açúcar-fosfato)
Hélice₁:
    x(t) = r * cos(ωt)
    y(t) = r * sin(ωt)
    z(t) = v * t

Hélice₂ (defasada 180°):
    x(t) = r * cos(ωt + π)
    y(t) = r * sin(ωt + π)
    z(t) = v * t

// Pares de bases (degraus)
Base_i conecta Hélice₁(t_i) a Hélice₂(t_i)

Parâmetros:
- r = 1nm (raio da hélice)
- Passo = 3.4nm (uma volta completa)
- 10 pares de bases por volta
- ω = 2π / passo
- v = passo / (2π)
```

```javascript
function createDNAHelix(turns, radius, pitch) {
    const backbone1 = [];
    const backbone2 = [];
    const basePairs = [];

    const pointsPerTurn = 20;
    const totalPoints = turns * pointsPerTurn;

    for (let i = 0; i <= totalPoints; i++) {
        const t = (i / pointsPerTurn) * Math.PI * 2;
        const z = (i / pointsPerTurn) * pitch;

        // Hélice 1
        backbone1.push(new THREE.Vector3(
            radius * Math.cos(t),
            radius * Math.sin(t),
            z
        ));

        // Hélice 2 (180° defasada)
        backbone2.push(new THREE.Vector3(
            radius * Math.cos(t + Math.PI),
            radius * Math.sin(t + Math.PI),
            z
        ));

        // Par de bases a cada 36° (10 por volta)
        if (i % 2 === 0) {
            basePairs.push({
                start: backbone1[i],
                end: backbone2[i],
                type: ['AT', 'TA', 'GC', 'CG'][Math.floor(Math.random() * 4)]
            });
        }
    }

    return { backbone1, backbone2, basePairs };
}
```

---

## 3. Técnicas de Combinação

### 3.1 Signed Distance Functions (SDF)
Para combinar formas suavemente:

```
// União suave
smoothUnion(d1, d2, k) = -log(exp(-k*d1) + exp(-k*d2)) / k

// Interseção suave
smoothIntersection(d1, d2, k) = -smoothUnion(-d1, -d2, k)

// Subtração suave
smoothSubtraction(d1, d2, k) = smoothIntersection(d1, -d2, k)
```

### 3.2 Metaballs (já implementado)
Para formas orgânicas que se fundem:

```
f(x, y, z) = Σᵢ (rᵢ² / ((x-xᵢ)² + (y-yᵢ)² + (z-zᵢ)²))

Superfície onde f(x,y,z) = threshold
```

---

## 4. Tabela de Referência Rápida

| Organela | Forma Base | Parâmetros Principais | Complexidade |
|----------|------------|----------------------|--------------|
| Núcleo | Esfera + ruído | R=5μm, noise=0.1 | Média |
| Mitocôndria | Cápsula curvada | L=3μm, r=0.5μm | Alta |
| Cloroplasto | Elipsóide oblato | a=4μm, c=1.5μm | Alta |
| RE | L-system tubos | iter=4, r=0.1μm | Muito Alta |
| Golgi | Pilha cisternas | n=6, curv=0.3 | Média |
| Vacúolo | Esfera irregular | R=10μm, irreg=0.1 | Baixa |
| DNA | Dupla hélice | r=1nm, pitch=3.4nm | Média |

---

## 5. Próximos Passos

1. [ ] Implementar biblioteca `OrganelleGeometry.js`
2. [ ] Integrar Simplex Noise para deformações
3. [ ] Criar shaders específicos por organela
4. [ ] Adicionar animações biológicas (ex: DNA replicação)
5. [ ] Implementar LOD (Level of Detail) para performance

---

## Referências

- Alberts et al. "Molecular Biology of the Cell" - dimensões celulares
- Three.js Documentation - geometrias paramétricas
- "Real-Time Rendering" - técnicas de SDF
- Perlin, K. "Improving Noise" - algoritmos de ruído
