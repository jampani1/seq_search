/**
 * OrganelleGeometry.js
 * Biblioteca de geometrias matemáticas para organelas celulares
 * Compatível com Three.js r128+
 */

// ============================================
// SIMPLEX NOISE (implementação simplificada)
// ============================================
const SimplexNoise = (function() {
    const F3 = 1.0 / 3.0;
    const G3 = 1.0 / 6.0;

    const grad3 = [
        [1,1,0],[-1,1,0],[1,-1,0],[-1,-1,0],
        [1,0,1],[-1,0,1],[1,0,-1],[-1,0,-1],
        [0,1,1],[0,-1,1],[0,1,-1],[0,-1,-1]
    ];

    const p = [];
    const perm = [];

    // Inicializar permutação
    for (let i = 0; i < 256; i++) {
        p[i] = Math.floor(Math.random() * 256);
    }
    for (let i = 0; i < 512; i++) {
        perm[i] = p[i & 255];
    }

    function dot3(g, x, y, z) {
        return g[0]*x + g[1]*y + g[2]*z;
    }

    return {
        noise3D: function(x, y, z) {
            let n0, n1, n2, n3;

            const s = (x + y + z) * F3;
            const i = Math.floor(x + s);
            const j = Math.floor(y + s);
            const k = Math.floor(z + s);

            const t = (i + j + k) * G3;
            const X0 = i - t;
            const Y0 = j - t;
            const Z0 = k - t;
            const x0 = x - X0;
            const y0 = y - Y0;
            const z0 = z - Z0;

            let i1, j1, k1, i2, j2, k2;

            if (x0 >= y0) {
                if (y0 >= z0) { i1=1; j1=0; k1=0; i2=1; j2=1; k2=0; }
                else if (x0 >= z0) { i1=1; j1=0; k1=0; i2=1; j2=0; k2=1; }
                else { i1=0; j1=0; k1=1; i2=1; j2=0; k2=1; }
            } else {
                if (y0 < z0) { i1=0; j1=0; k1=1; i2=0; j2=1; k2=1; }
                else if (x0 < z0) { i1=0; j1=1; k1=0; i2=0; j2=1; k2=1; }
                else { i1=0; j1=1; k1=0; i2=1; j2=1; k2=0; }
            }

            const x1 = x0 - i1 + G3;
            const y1 = y0 - j1 + G3;
            const z1 = z0 - k1 + G3;
            const x2 = x0 - i2 + 2.0*G3;
            const y2 = y0 - j2 + 2.0*G3;
            const z2 = z0 - k2 + 2.0*G3;
            const x3 = x0 - 1.0 + 3.0*G3;
            const y3 = y0 - 1.0 + 3.0*G3;
            const z3 = z0 - 1.0 + 3.0*G3;

            const ii = i & 255;
            const jj = j & 255;
            const kk = k & 255;

            let t0 = 0.6 - x0*x0 - y0*y0 - z0*z0;
            if (t0 < 0) n0 = 0.0;
            else {
                t0 *= t0;
                n0 = t0 * t0 * dot3(grad3[perm[ii+perm[jj+perm[kk]]] % 12], x0, y0, z0);
            }

            let t1 = 0.6 - x1*x1 - y1*y1 - z1*z1;
            if (t1 < 0) n1 = 0.0;
            else {
                t1 *= t1;
                n1 = t1 * t1 * dot3(grad3[perm[ii+i1+perm[jj+j1+perm[kk+k1]]] % 12], x1, y1, z1);
            }

            let t2 = 0.6 - x2*x2 - y2*y2 - z2*z2;
            if (t2 < 0) n2 = 0.0;
            else {
                t2 *= t2;
                n2 = t2 * t2 * dot3(grad3[perm[ii+i2+perm[jj+j2+perm[kk+k2]]] % 12], x2, y2, z2);
            }

            let t3 = 0.6 - x3*x3 - y3*y3 - z3*z3;
            if (t3 < 0) n3 = 0.0;
            else {
                t3 *= t3;
                n3 = t3 * t3 * dot3(grad3[perm[ii+1+perm[jj+1+perm[kk+1]]] % 12], x3, y3, z3);
            }

            return 32.0 * (n0 + n1 + n2 + n3);
        }
    };
})();

// ============================================
// CLASSE PRINCIPAL
// ============================================
class OrganelleGeometry {

    /**
     * Núcleo - Esfera com deformação orgânica
     * @param {number} radius - Raio base (default: 1)
     * @param {number} detail - Subdivisões (default: 4)
     * @param {number} noiseScale - Escala do ruído (default: 2)
     * @param {number} noiseAmount - Amplitude da deformação (default: 0.1)
     */
    static createNucleus(radius = 1, detail = 4, noiseScale = 2, noiseAmount = 0.1) {
        const geometry = new THREE.IcosahedronGeometry(radius, detail);
        const positions = geometry.attributes.position;

        for (let i = 0; i < positions.count; i++) {
            const x = positions.getX(i);
            const y = positions.getY(i);
            const z = positions.getZ(i);

            const noise = SimplexNoise.noise3D(
                x * noiseScale,
                y * noiseScale,
                z * noiseScale
            ) * noiseAmount;

            const scale = 1 + noise;
            positions.setXYZ(i, x * scale, y * scale, z * scale);
        }

        geometry.computeVertexNormals();
        return geometry;
    }

    /**
     * Mitocôndria - Cápsula alongada com curvatura natural
     * @param {number} length - Comprimento total
     * @param {number} radius - Raio do tubo
     * @param {number} curvature - Quantidade de curvatura (0-1)
     */
    static createMitochondria(length = 2, radius = 0.3, curvature = 0.3) {
        const points = [];
        const segments = 8;

        for (let i = 0; i <= segments; i++) {
            const t = i / segments;
            const x = (t - 0.5) * length;

            // Curvatura senoidal natural
            const y = Math.sin(t * Math.PI) * curvature * length * 0.2;
            const z = Math.sin(t * Math.PI * 2) * curvature * length * 0.1;

            points.push(new THREE.Vector3(x, y, z));
        }

        const curve = new THREE.CatmullRomCurve3(points);
        const geometry = new THREE.TubeGeometry(curve, 32, radius, 16, false);

        // Adicionar caps esféricos nas pontas
        return geometry;
    }

    /**
     * Cloroplasto - Elipsóide achatado (forma de lente)
     * @param {number} radiusX - Raio maior
     * @param {number} radiusZ - Espessura (menor que radiusX)
     */
    static createChloroplast(radiusX = 1.5, radiusZ = 0.5) {
        const geometry = new THREE.SphereGeometry(radiusX, 32, 32);
        const positions = geometry.attributes.position;

        // Achatar em Z
        for (let i = 0; i < positions.count; i++) {
            const z = positions.getZ(i);
            positions.setZ(i, z * (radiusZ / radiusX));
        }

        geometry.computeVertexNormals();
        return geometry;
    }

    /**
     * Granum (pilha de tilacóides dentro do cloroplasto)
     * @param {number} radius - Raio dos discos
     * @param {number} layers - Número de camadas
     * @param {number} spacing - Espaçamento entre camadas
     */
    static createGranum(radius = 0.15, layers = 10, spacing = 0.015) {
        const group = new THREE.Group();

        for (let i = 0; i < layers; i++) {
            const disc = new THREE.CylinderGeometry(radius, radius, 0.008, 16);
            const mesh = new THREE.Mesh(disc);
            mesh.position.y = i * spacing - (layers * spacing / 2);
            group.add(mesh);
        }

        return group;
    }

    /**
     * Vacúolo - Grande esfera irregular
     * @param {number} radius - Raio base
     * @param {number} irregularity - Quantidade de irregularidade (0-0.3)
     */
    static createVacuole(radius = 3, irregularity = 0.15) {
        const geometry = new THREE.IcosahedronGeometry(radius, 4);
        const positions = geometry.attributes.position;

        for (let i = 0; i < positions.count; i++) {
            const x = positions.getX(i);
            const y = positions.getY(i);
            const z = positions.getZ(i);

            // Múltiplas frequências de ruído para aparência orgânica
            const noise =
                0.5 * SimplexNoise.noise3D(x * 0.5, y * 0.5, z * 0.5) +
                0.3 * SimplexNoise.noise3D(x * 1, y * 1, z * 1) +
                0.2 * SimplexNoise.noise3D(x * 2, y * 2, z * 2);

            const scale = 1 + noise * irregularity;
            positions.setXYZ(i, x * scale, y * scale, z * scale);
        }

        geometry.computeVertexNormals();
        return geometry;
    }

    /**
     * DNA Dupla Hélice
     * @param {number} turns - Número de voltas
     * @param {number} radius - Raio da hélice
     * @param {number} pitch - Passo (altura de uma volta)
     * @param {number} tubeRadius - Espessura do backbone
     */
    static createDNAHelix(turns = 3, radius = 0.5, pitch = 1, tubeRadius = 0.05) {
        const group = new THREE.Group();
        const pointsPerTurn = 30;
        const totalPoints = turns * pointsPerTurn;

        // Pontos para os dois backbones
        const backbone1Points = [];
        const backbone2Points = [];

        for (let i = 0; i <= totalPoints; i++) {
            const t = (i / pointsPerTurn) * Math.PI * 2;
            const z = (i / pointsPerTurn) * pitch;

            backbone1Points.push(new THREE.Vector3(
                radius * Math.cos(t),
                radius * Math.sin(t),
                z
            ));

            backbone2Points.push(new THREE.Vector3(
                radius * Math.cos(t + Math.PI),
                radius * Math.sin(t + Math.PI),
                z
            ));
        }

        // Criar tubos para backbones
        const curve1 = new THREE.CatmullRomCurve3(backbone1Points);
        const curve2 = new THREE.CatmullRomCurve3(backbone2Points);

        const backbone1Geo = new THREE.TubeGeometry(curve1, totalPoints * 2, tubeRadius, 8, false);
        const backbone2Geo = new THREE.TubeGeometry(curve2, totalPoints * 2, tubeRadius, 8, false);

        group.add(new THREE.Mesh(backbone1Geo));
        group.add(new THREE.Mesh(backbone2Geo));

        // Pares de bases (conexões entre backbones)
        const basePairColors = {
            'AT': 0x4CAF50,  // Verde
            'TA': 0x8BC34A,  // Verde claro
            'GC': 0x2196F3,  // Azul
            'CG': 0x03A9F4   // Azul claro
        };
        const types = ['AT', 'TA', 'GC', 'CG'];

        for (let i = 0; i < totalPoints; i += 3) {
            const p1 = backbone1Points[i];
            const p2 = backbone2Points[i];

            const direction = new THREE.Vector3().subVectors(p2, p1);
            const length = direction.length();

            const basePair = new THREE.CylinderGeometry(tubeRadius * 0.8, tubeRadius * 0.8, length, 8);
            const mesh = new THREE.Mesh(basePair);

            mesh.position.copy(p1).add(direction.multiplyScalar(0.5));
            mesh.lookAt(p2);
            mesh.rotateX(Math.PI / 2);

            // Cor baseada no tipo
            mesh.userData.baseType = types[Math.floor(Math.random() * 4)];

            group.add(mesh);
        }

        return group;
    }

    /**
     * Complexo de Golgi - Pilha de cisternas curvadas
     * @param {number} layers - Número de cisternas
     * @param {number} width - Largura das cisternas
     */
    static createGolgi(layers = 6, width = 1.5) {
        const group = new THREE.Group();
        const spacing = 0.12;

        for (let i = 0; i < layers; i++) {
            // Curvatura diminui da cis (topo) para trans (base)
            const curvature = 0.4 - (i * 0.05);
            const cisterna = this._createCisterna(width, width * 0.4, curvature);
            cisterna.position.y = i * spacing;
            group.add(cisterna);

            // Vesículas entre camadas
            if (i < layers - 1) {
                for (let v = 0; v < 3; v++) {
                    const vesicle = new THREE.SphereGeometry(0.04, 8, 8);
                    const mesh = new THREE.Mesh(vesicle);
                    mesh.position.set(
                        (Math.random() - 0.5) * width * 0.8,
                        i * spacing + spacing * 0.5,
                        (Math.random() - 0.5) * width * 0.3
                    );
                    group.add(mesh);
                }
            }
        }

        return group;
    }

    /**
     * Cisterna individual do Golgi - disco curvado 3D
     * @private
     */
    static _createCisterna(width, depth, curvature) {
        // Usar cilindro fino como base (tem volume 3D real)
        const geometry = new THREE.CylinderGeometry(
            width / 2,      // radiusTop
            width / 2,      // radiusBottom
            0.03,           // height (espessura fina mas visível)
            32,             // radialSegments
            8               // heightSegments para deformação suave
        );

        const positions = geometry.attributes.position;

        // Aplicar curvatura parabólica - centro mais alto, bordas mais baixas
        for (let i = 0; i < positions.count; i++) {
            const x = positions.getX(i);
            const z = positions.getZ(i);
            const radius = width / 2;

            // Distância normalizada do centro (0 no centro, 1 na borda)
            const distFromCenter = Math.sqrt(x * x + z * z) / radius;

            // Curvatura parabólica: máxima no centro, zero na borda
            const yOffset = curvature * (1 - distFromCenter * distFromCenter);
            positions.setY(i, positions.getY(i) + yOffset);
        }

        geometry.computeVertexNormals();
        return new THREE.Mesh(geometry);
    }

    /**
     * Retículo Endoplasmático - Rede de tubos
     * @param {number} iterations - Iterações do L-system (2-4)
     * @param {number} segmentLength - Comprimento de cada segmento
     * @param {number} tubeRadius - Raio dos tubos
     */
    static createER(iterations = 3, segmentLength = 0.3, tubeRadius = 0.03) {
        const group = new THREE.Group();

        // L-system rules
        const rules = { 'F': 'F[+F][-F]F[^F]' };
        let axiom = 'F';

        // Gerar string L-system
        for (let i = 0; i < iterations; i++) {
            let newAxiom = '';
            for (const char of axiom) {
                newAxiom += rules[char] || char;
            }
            axiom = newAxiom;
        }

        // Interpretar L-system
        const stack = [];
        let position = new THREE.Vector3(0, 0, 0);
        let direction = new THREE.Vector3(0, 1, 0);
        const angle = Math.PI / 6;

        const tubes = [];
        let currentPath = [position.clone()];

        for (const char of axiom) {
            switch (char) {
                case 'F':
                    const newPos = position.clone().add(
                        direction.clone().multiplyScalar(segmentLength)
                    );
                    currentPath.push(newPos.clone());
                    position = newPos;
                    break;

                case '+':
                    direction.applyAxisAngle(new THREE.Vector3(0, 0, 1), angle);
                    break;

                case '-':
                    direction.applyAxisAngle(new THREE.Vector3(0, 0, 1), -angle);
                    break;

                case '^':
                    direction.applyAxisAngle(new THREE.Vector3(1, 0, 0), angle);
                    break;

                case '[':
                    stack.push({
                        pos: position.clone(),
                        dir: direction.clone(),
                        path: currentPath.slice()
                    });
                    break;

                case ']':
                    // Criar tubo do path atual
                    if (currentPath.length >= 2) {
                        tubes.push(currentPath.slice());
                    }

                    const state = stack.pop();
                    position = state.pos;
                    direction = state.dir;
                    currentPath = [position.clone()];
                    break;
            }
        }

        // Criar geometrias dos tubos
        tubes.forEach(path => {
            if (path.length >= 2) {
                const curve = new THREE.CatmullRomCurve3(path);
                const tubeGeo = new THREE.TubeGeometry(curve, path.length * 4, tubeRadius, 6, false);
                group.add(new THREE.Mesh(tubeGeo));
            }
        });

        return group;
    }

    /**
     * Membrana Celular - Superfície com ondulações
     * @param {number} width - Largura
     * @param {number} height - Altura
     * @param {number} waveAmount - Intensidade das ondulações
     */
    static createMembrane(width = 5, height = 5, waveAmount = 0.1) {
        const geometry = new THREE.PlaneGeometry(width, height, 50, 50);
        const positions = geometry.attributes.position;

        for (let i = 0; i < positions.count; i++) {
            const x = positions.getX(i);
            const y = positions.getY(i);

            const z = SimplexNoise.noise3D(x * 2, y * 2, 0) * waveAmount +
                      SimplexNoise.noise3D(x * 5, y * 5, 0) * waveAmount * 0.3;

            positions.setZ(i, z);
        }

        geometry.computeVertexNormals();
        return geometry;
    }

    /**
     * Ribossomo - Pequena esfera com duas subunidades
     * @param {number} scale - Escala geral
     */
    static createRibosome(scale = 0.05) {
        const group = new THREE.Group();

        // Subunidade maior (60S)
        const large = new THREE.SphereGeometry(scale, 8, 8);
        const largeMesh = new THREE.Mesh(large);
        group.add(largeMesh);

        // Subunidade menor (40S)
        const small = new THREE.SphereGeometry(scale * 0.7, 8, 8);
        const smallMesh = new THREE.Mesh(small);
        smallMesh.position.y = scale * 1.2;
        group.add(smallMesh);

        return group;
    }
}

// Exportar para uso global
if (typeof window !== 'undefined') {
    window.OrganelleGeometry = OrganelleGeometry;
    window.SimplexNoise = SimplexNoise;
}

// Exportar para módulos ES6
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { OrganelleGeometry, SimplexNoise };
}
