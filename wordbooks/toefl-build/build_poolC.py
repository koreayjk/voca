#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json, collections

# Each entry: (en, pos, ko, level, topic)
# topics: 화학 physics 물리 astronomy 천문 geology 지구과학 environmental 환경
W = []

def add(en, pos, ko, level, topic):
    W.append((en, pos, ko, level, topic))

# =========================================================
# CHEMISTRY  화학
# =========================================================
CHEM = [
("molecule","n","분자","B2"),("compound","n","화합물","B2"),("solvent","n","용매","C1"),
("catalyst","n","촉매","C1"),("oxidation","n","산화","C1"),("isotope","n","동위원소","C1"),
("atom","n","원자","B2"),("element","n","원소","B2"),("reaction","n","반응","B2"),
("bond","n","결합","B2"),("ion","n","이온","C1"),("acid","n","산","B2"),
("alkaline","adj","알칼리성의","C1"),("alkali","n","알칼리","C1"),("base","n","염기","B2"),
("neutral","adj","중성의","B2"),("neutralize","v","중화하다","C1"),("dissolve","v","용해하다","B2"),
("soluble","adj","용해성의","C1"),("solubility","n","용해도","C1"),("insoluble","adj","불용성의","C1"),
("saturate","v","포화시키다","C1"),("saturation","n","포화","C1"),("concentration","n","농도","B2"),
("dilute","v","희석하다","C1"),("dilution","n","희석","C1"),("suspension","n","현탁액","C1"),
("solution","n","용액","B2"),("mixture","n","혼합물","B2"),("substance","n","물질","B2"),
("particle","n","입자","B2"),("nucleus","n","핵","C1"),("proton","n","양성자","C1"),
("neutron","n","중성자","C1"),("electron","n","전자","B2"),("valence","n","원자가","C2"),
("orbital","n","궤도함수","C2"),("configuration","n","배열","C1"),("periodic","adj","주기적인","C1"),
("reactivity","n","반응성","C1"),("reactant","n","반응물","C1"),("reagent","n","시약","C2"),
("product","n","생성물","B2"),("yield","n","수율","C1"),("equilibrium","n","평형","C1"),
("reversible","adj","가역적인","C1"),("irreversible","adj","비가역적인","C1"),("exothermic","adj","발열의","C2"),
("endothermic","adj","흡열의","C2"),("combustion","n","연소","C1"),("ignite","v","점화하다","C1"),
("flammable","adj","가연성의","C1"),("corrosive","adj","부식성의","C1"),("corrode","v","부식하다","C1"),
("corrosion","n","부식","C1"),("rust","v","녹슬다","B2"),("tarnish","v","변색되다","C2"),
("precipitate","v","침전시키다","C2"),("precipitation","n","침전","C1"),("crystalline","adj","결정질의","C1"),
("crystallize","v","결정화하다","C1"),("crystallization","n","결정화","C1"),("lattice","n","격자","C2"),
("polymer","n","중합체","C1"),("monomer","n","단량체","C2"),("polymerization","n","중합","C2"),
("macromolecule","n","고분자","C2"),("hydrocarbon","n","탄화수소","C1"),("organic","adj","유기의","B2"),
("inorganic","adj","무기의","C1"),("synthesis","n","합성","C1"),("synthesize","v","합성하다","C1"),
("synthetic","adj","합성의","B2"),("decompose","v","분해하다","C1"),("decomposition","n","분해","C1"),
("distillation","n","증류","C1"),("distill","v","증류하다","C1"),("filtration","n","여과","C1"),
("filter","v","여과하다","B2"),("evaporate","v","증발하다","B2"),("evaporation","n","증발","B2"),
("condense","v","응축하다","B2"),("condensation","n","응축","C1"),("sublimation","n","승화","C2"),
("vaporize","v","기화하다","C1"),("vapor","n","증기","B2"),("gaseous","adj","기체의","C1"),
("liquid","n","액체","B2"),("solid","n","고체","B2"),("state","n","상태","B2"),
("phase","n","상","B2"),("density","n","밀도","B2"),("viscosity","n","점성","C1"),
("viscous","adj","점성의","C1"),("fluid","n","유체","B2"),("miscible","adj","혼화성의","C2"),
("emulsion","n","유화액","C2"),("colloid","n","콜로이드","C2"),("aqueous","adj","수용성의","C2"),
("hydrogen","n","수소","B2"),("oxygen","n","산소","B2"),("carbon","n","탄소","B2"),
("nitrogen","n","질소","B2"),("sulfur","n","황","C1"),("chlorine","n","염소","C1"),
("sodium","n","나트륨","C1"),("potassium","n","칼륨","C1"),("calcium","n","칼슘","B2"),
("magnesium","n","마그네슘","C1"),("phosphorus","n","인","C1"),("helium","n","헬륨","B2"),
("metallic","adj","금속의","B2"),("alloy","n","합금","C1"),("oxide","n","산화물","C1"),
("hydroxide","n","수산화물","C2"),("chloride","n","염화물","C1"),("sulfate","n","황산염","C2"),
("nitrate","n","질산염","C1"),("carbonate","n","탄산염","C1"),("salt","n","염","B2"),
("compoundize","v","화합시키다","C2"),("reduce","v","환원하다","B2"),("reduction","n","환원","B2"),
("oxidize","v","산화하다","C1"),("oxidant","n","산화제","C2"),("antioxidant","n","항산화제","C1"),
("catalyze","v","촉매작용하다","C1"),("catalytic","adj","촉매의","C1"),("enzyme","n","효소","B2"),
("substrate","n","기질","C2"),("acidity","n","산성","C1"),("alkalinity","n","알칼리성","C2"),
("buffer","n","완충액","C1"),("titration","n","적정","C2"),("stoichiometry","n","화학량론","C2"),
("mole","n","몰","C1"),("molar","adj","몰의","C2"),("molarity","n","몰농도","C2"),
("formula","n","화학식","B2"),("equation","n","반응식","B2"),("coefficient","n","계수","C1"),
("radical","n","라디칼","C2"),("bonding","n","결합","B2"),("covalent","adj","공유의","C1"),
("ionic","adj","이온의","C1"),("electronegativity","n","전기음성도","C2"),("polarity","n","극성","C1"),
("polar","adj","극성의","C1"),("nonpolar","adj","무극성의","C2"),("dipole","n","쌍극자","C2"),
("hydration","n","수화","C2"),("dehydration","n","탈수","C1"),("hydrolysis","n","가수분해","C2"),
("fermentation","n","발효","C1"),("ferment","v","발효하다","C1"),("respiration","n","호흡","B2"),
("photosynthesis","n","광합성","B2"),("metabolism","n","신진대사","B2"),("compound","adj","복합의","B2"),
("purity","n","순도","C1"),("purify","v","정제하다","C1"),("impurity","n","불순물","C1"),
("contaminant","n","오염물질","C1"),("residue","n","잔류물","C1"),("byproduct","n","부산물","C1"),
("derivative","n","유도체","C1"),("compoundment","n","화합","C2"),("adhesion","n","접착","C1"),
("cohesion","n","응집","C1"),("adhesive","adj","접착성의","B2"),("bonded","adj","결합된","B2"),
("volatile","adj","휘발성의","C1"),("volatility","n","휘발성","C2"),("inert","adj","비활성의","C1"),
("reactive","adj","반응성의","C1"),("noble","adj","비활성(기체)의","C1"),("stable","adj","안정한","B2"),
("stability","n","안정성","B2"),("unstable","adj","불안정한","B2"),("decay","v","붕괴하다","B2"),
("radioactive","adj","방사성의","C1"),("radioactivity","n","방사능","C1"),("halflife","n","반감기","C2"),
("fission","n","핵분열","C1"),("fusion","n","핵융합","C1"),("mass","n","질량","B2"),
("weight","n","무게","B2"),("spectrum","n","스펙트럼","C1"),("spectroscopy","n","분광학","C2"),
("chromatography","n","크로마토그래피","C2"),("assay","n","분석시험","C2"),("analyte","n","분석물","C2"),
("qualitative","adj","정성적인","C1"),("quantitative","adj","정량적인","C1"),("calibrate","v","교정하다","C1"),
("dissociate","v","해리하다","C2"),("dissociation","n","해리","C2"),("ionization","n","이온화","C1"),
("electrolysis","n","전기분해","C1"),("electrolyte","n","전해질","C1"),("conductivity","n","전도성","C1"),
("conductor","n","도체","B2"),("insulator","n","절연체","B2"),("semiconductor","n","반도체","C1"),
("bleach","v","표백하다","B2"),("dye","n","염료","B2"),("pigment","n","색소","C1"),
("compoundable","adj","화합가능한","C2"),("effervescent","adj","발포성의","C2"),("caustic","adj","부식성의","C2"),
("acrid","adj","자극적인","C2"),("pungent","adj","자극성의","C1"),("odorless","adj","무취의","C1"),
("combustible","adj","가연성의","C1"),("incombustible","adj","불연성의","C2"),("oxidative","adj","산화적인","C2"),
("reductive","adj","환원적인","C2"),("thermodynamics","n","열역학","C2"),("enthalpy","n","엔탈피","C2"),
("entropy","n","엔트로피","C2"),("kinetics","n","반응속도론","C2"),("activation","n","활성화","C1"),
("inhibitor","n","억제제","C1"),("mediate","v","매개하다","C1"),("compoundary","adj","화합의","C2"),
("chelate","v","킬레이트화하다","C2"),("amorphous","adj","비정질의","C2"),("allotrope","n","동소체","C2"),
]
for e,p,k,l in CHEM:
    add(e,p,k,l,"화학")

# =========================================================
# PHYSICS  물리
# =========================================================
PHYS = [
("velocity","n","속도","B2"),("momentum","n","운동량","C1"),("friction","n","마찰","B2"),
("radiation","n","방사선","B2"),("magnitude","n","크기","B2"),("wavelength","n","파장","B2"),
("acceleration","n","가속도","B2"),("accelerate","v","가속하다","B2"),("decelerate","v","감속하다","C1"),
("inertia","n","관성","C1"),("gravity","n","중력","B2"),("gravitation","n","만유인력","C1"),
("mass","n","질량","B2"),("force","n","힘","B2"),("energy","n","에너지","B2"),
("kinetic","adj","운동의","C1"),("potential","adj","위치의","B2"),("work","n","일","B2"),
("power","n","동력","B2"),("torque","n","토크","C2"),("displacement","n","변위","C1"),
("trajectory","n","궤적","C1"),("projectile","n","발사체","C1"),("amplitude","n","진폭","C1"),
("frequency","n","진동수","B2"),("oscillation","n","진동","C1"),("oscillate","v","진동하다","C1"),
("vibration","n","진동","B2"),("vibrate","v","진동하다","B2"),("resonance","n","공명","C1"),
("harmonic","adj","조화의","C2"),("wave","n","파동","B2"),("crest","n","마루","C1"),
("trough","n","골","C1"),("interference","n","간섭","C1"),("diffraction","n","회절","C2"),
("refraction","n","굴절","C1"),("refract","v","굴절시키다","C1"),("reflection","n","반사","B2"),
("reflect","v","반사하다","B2"),("absorption","n","흡수","B2"),("absorb","v","흡수하다","B2"),
("transmission","n","투과","B2"),("transmit","v","전달하다","B2"),("propagate","v","전파하다","C1"),
("propagation","n","전파","C1"),("medium","n","매질","B2"),("vacuum","n","진공","B2"),
("pressure","n","압력","B2"),("compression","n","압축","C1"),("compress","v","압축하다","B2"),
("tension","n","장력","B2"),("elasticity","n","탄성","C1"),("elastic","adj","탄성의","B2"),
("plasticity","n","소성","C2"),("deformation","n","변형","C1"),("deform","v","변형시키다","C1"),
("stress","n","응력","B2"),("strain","n","변형률","C1"),("rigid","adj","단단한","B2"),
("rigidity","n","강성","C1"),("buoyancy","n","부력","C1"),("buoyant","adj","부력있는","C2"),
("density","n","밀도","B2"),("thermal","adj","열의","B2"),("conduction","n","전도","C1"),
("convection","n","대류","C1"),("insulation","n","단열","B2"),("temperature","n","온도","B2"),
("heat","n","열","B2"),("calorie","n","칼로리","B2"),("joule","n","줄","C1"),
("watt","n","와트","B2"),("newton","n","뉴턴","C1"),("magnitude","adj","크기의","B2"),
("charge","n","전하","B2"),("current","n","전류","B2"),("voltage","n","전압","B2"),
("resistance","n","저항","B2"),("resistor","n","저항기","C1"),("circuit","n","회로","B2"),
("capacitor","n","축전기","C1"),("capacitance","n","전기용량","C2"),("inductance","n","인덕턴스","C2"),
("magnetism","n","자성","B2"),("magnetic","adj","자기의","B2"),("magnetize","v","자화하다","C1"),
("magnet","n","자석","B2"),("field","n","장","B2"),("flux","n","선속","C2"),
("polarity","n","극성","C1"),("electromagnetic","adj","전자기의","C1"),("electromagnetism","n","전자기학","C2"),
("photon","n","광자","C1"),("quantum","n","양자","C1"),("relativity","n","상대성","C1"),
("spectrum","n","스펙트럼","C1"),("infrared","adj","적외선의","C1"),("ultraviolet","adj","자외선의","C1"),
("microwave","n","마이크로파","B2"),("gamma","adj","감마의","C1"),("wavefront","n","파면","C2"),
("luminous","adj","발광하는","C1"),("luminescence","n","발광","C2"),("fluorescence","n","형광","C2"),
("phosphorescence","n","인광","C2"),("optics","n","광학","C1"),("optical","adj","광학의","C1"),
("lens","n","렌즈","B2"),("prism","n","프리즘","C1"),("concave","adj","오목한","C1"),
("convex","adj","볼록한","C1"),("focal","adj","초점의","C1"),("focus","n","초점","B2"),
("aperture","n","조리개","C2"),("intensity","n","강도","B2"),("luminosity","n","광도","C1"),
("brightness","n","밝기","B2"),("contrast","n","대비","B2"),("scatter","v","산란하다","B2"),
("scattering","n","산란","C1"),("deflect","v","편향시키다","C1"),("deflection","n","편향","C1"),
("equilibrium","n","평형","C1"),("stationary","adj","정지한","B2"),("motion","n","운동","B2"),
("rotation","n","회전","B2"),("rotate","v","회전하다","B2"),("revolution","n","공전","B2"),
("revolve","v","공전하다","B2"),("centripetal","adj","구심의","C2"),("centrifugal","adj","원심의","C2"),
("angular","adj","각의","C1"),("linear","adj","선형의","B2"),("nonlinear","adj","비선형의","C2"),
("vector","n","벡터","C1"),("scalar","n","스칼라","C2"),("magnitudeless","adj","크기없는","C2"),
("gradient","n","기울기","C1"),("coefficient","n","계수","C1"),("dimension","n","차원","B2"),
("dimensional","adj","차원의","C1"),("quantify","v","정량화하다","C1"),("measurement","n","측정","B2"),
("calibrate","v","교정하다","C1"),("precision","n","정밀도","C1"),("accuracy","n","정확도","B2"),
("threshold","n","임계값","C1"),("critical","adj","임계의","B2"),("phenomenon","n","현상","B2"),
("empirical","adj","경험적인","C1"),("hypothesis","n","가설","B2"),("theoretical","adj","이론적인","B2"),
("conservation","n","보존","B2"),("dissipate","v","소산하다","C1"),("dissipation","n","소산","C2"),
("efficiency","n","효율","B2"),("output","n","출력","B2"),("input","n","입력","B2"),
("mechanism","n","기제","B2"),("mechanical","adj","기계적인","B2"),("mechanics","n","역학","C1"),
("dynamics","n","동역학","C1"),("statics","n","정역학","C2"),("kinematics","n","운동학","C2"),
("pendulum","n","진자","C1"),("gyroscope","n","자이로스코프","C2"),("lever","n","지레","B2"),
("fulcrum","n","받침점","C1"),("pulley","n","도르래","B2"),("gear","n","기어","B2"),
("axle","n","차축","B2"),("rotor","n","회전자","C2"),("turbine","n","터빈","B2"),
("piston","n","피스톤","B2"),("thrust","n","추진력","C1"),("propel","v","추진하다","C1"),
("propulsion","n","추진","C1"),("aerodynamics","n","공기역학","C2"),("drag","n","항력","C1"),
("lift","n","양력","B2"),("turbulence","n","난류","C1"),("laminar","adj","층류의","C2"),
("streamline","v","유선형으로하다","C1"),("nozzle","n","노즐","C1"),("valve","n","밸브","B2"),
("hydraulic","adj","수압의","C1"),("pneumatic","adj","공기압의","C2"),("mechanize","v","기계화하다","C1"),
("radiate","v","방사하다","B2"),("emit","v","방출하다","B2"),("emission","n","방출","B2"),
("emissivity","n","방사율","C2"),("attenuate","v","감쇠시키다","C2"),("attenuation","n","감쇠","C2"),
("threshold","adj","임계의","C1"),("saturate","v","포화시키다","C1"),("superconductor","n","초전도체","C2"),
("plasma","n","플라스마","C1"),("ionosphere","n","전리층","C2"),("dielectric","adj","유전체의","C2"),
("permeability","n","투자율","C2"),("permittivity","n","유전율","C2"),("wattage","n","전력량","C1"),
("amperage","n","전류량","C2"),("ohm","n","옴","C1"),("photoelectric","adj","광전의","C2"),
]
for e,p,k,l in PHYS:
    add(e,p,k,l,"물리")

# =========================================================
# ASTRONOMY & SPACE  천문
# =========================================================
ASTRO = [
("orbit","n","궤도","B2"),("galaxy","n","은하","B2"),("comet","n","혜성","B2"),
("gravitational","adj","중력의","C1"),("celestial","adj","천체의","C1"),("luminosity","n","광도","C1"),
("asteroid","n","소행성","B2"),("meteor","n","유성","B2"),("meteorite","n","운석","C1"),
("meteoroid","n","유성체","C2"),("nebula","n","성운","C1"),("constellation","n","별자리","B2"),
("cosmos","n","우주","C1"),("cosmic","adj","우주의","C1"),("cosmology","n","우주론","C2"),
("astronomy","n","천문학","B2"),("astronomical","adj","천문학의","B2"),("astronomer","n","천문학자","B2"),
("astrophysics","n","천체물리학","C2"),("planetary","adj","행성의","C1"),("planet","n","행성","B2"),
("satellite","n","위성","B2"),("lunar","adj","달의","C1"),("solar","adj","태양의","B2"),
("stellar","adj","항성의","C1"),("interstellar","adj","성간의","C1"),("intergalactic","adj","은하간의","C2"),
("supernova","n","초신성","C1"),("nova","n","신성","C2"),("pulsar","n","펄서","C2"),
("quasar","n","퀘이사","C2"),("blackhole","n","블랙홀","C1"),("singularity","n","특이점","C2"),
("eclipse","n","식","B2"),("solstice","n","지점","C1"),("equinox","n","분점","C1"),
("zenith","n","천정","C2"),("horizon","n","지평선","B2"),("azimuth","n","방위각","C2"),
("aphelion","n","원일점","C2"),("perihelion","n","근일점","C2"),("apogee","n","원지점","C2"),
("perigee","n","근지점","C2"),("elliptical","adj","타원의","C1"),("ellipse","n","타원","C1"),
("revolve","v","공전하다","B2"),("rotate","v","자전하다","B2"),("axis","n","자전축","B2"),
("tilt","n","기울기","B2"),("precession","n","세차운동","C2"),("trajectory","n","궤적","C1"),
("gravity","n","중력","B2"),("microgravity","n","미소중력","C2"),("weightlessness","n","무중력","C1"),
("astronaut","n","우주비행사","B2"),("cosmonaut","n","우주비행사","C1"),("spacecraft","n","우주선","B2"),
("probe","n","탐사선","B2"),("rover","n","탐사차","B2"),("module","n","모듈","B2"),
("launch","v","발사하다","B2"),("propellant","n","추진제","C2"),("payload","n","탑재물","C1"),
("thruster","n","추진기","C2"),("reentry","n","재진입","C1"),("telescope","n","망원경","B2"),
("observatory","n","천문대","B2"),("radio","adj","전파의","B2"),("spectrometer","n","분광기","C2"),
("radiometer","n","복사계","C2"),("parallax","n","시차","C2"),("redshift","n","적색편이","C2"),
("blueshift","n","청색편이","C2"),("doppler","adj","도플러의","C2"),("light-year","n","광년","B2"),
("parsec","n","파섹","C2"),("magnitude","n","등급","C1"),("albedo","n","반사율","C2"),
("radiance","n","복사휘도","C2"),("irradiance","n","조사도","C2"),("flare","n","플레어","C1"),
("prominence","n","홍염","C2"),("corona","n","코로나","C1"),("chromosphere","n","채층","C2"),
("photosphere","n","광구","C2"),("sunspot","n","흑점","C1"),("granule","n","쌀알조직","C2"),
("plasma","n","플라스마","C1"),("nucleosynthesis","n","핵합성","C2"),("accretion","n","강착","C2"),
("accrete","v","강착하다","C2"),("coalesce","v","합쳐지다","C1"),("condense","v","응축하다","B2"),
("protostar","n","원시별","C2"),("protoplanet","n","원시행성","C2"),("planetesimal","n","미행성","C2"),
("dwarf","adj","왜성의","C1"),("giant","adj","거성의","B2"),("terrestrial","adj","지구형의","C1"),
("gaseous","adj","기체의","C1"),("crater","n","분화구","B2"),("regolith","n","표토","C2"),
("mantle","n","맨틀","C1"),("core","n","핵","B2"),("crust","n","지각","B2"),
("orbital","adj","궤도의","C1"),("geostationary","adj","정지궤도의","C2"),("geosynchronous","adj","지구동기의","C2"),
("hemisphere","n","반구","B2"),("latitude","n","위도","B2"),("longitude","n","경도","B2"),
("meridian","n","자오선","C1"),("celestial","n","천구","C1"),("firmament","n","창공","C2"),
("void","n","공동","C1"),("expansion","n","팽창","B2"),("expand","v","팽창하다","B2"),
("contract","v","수축하다","B2"),("collapse","v","붕괴하다","B2"),("dense","adj","밀집한","B2"),
("diffuse","adj","확산된","C1"),("radiate","v","방사하다","B2"),("radial","adj","방사상의","C1"),
("gravitate","v","끌리다","C1"),("orbiter","n","궤도선","C1"),("lander","n","착륙선","C1"),
("docking","n","도킹","C1"),("tether","n","연결끈","C2"),("cosmological","adj","우주론의","C2"),
("nebular","adj","성운의","C2"),("galactic","adj","은하의","C1"),("extraterrestrial","adj","외계의","C1"),
("astrobiology","n","우주생물학","C2"),("habitable","adj","거주가능한","C1"),("exoplanet","n","외계행성","C1"),
("transit","n","통과","C1"),("occultation","n","엄폐","C2"),("conjunction","n","합","C2"),
("opposition","n","충","C1"),("phase","n","위상","B2"),("waxing","adj","차오르는","C2"),
("waning","adj","기우는","C2"),("crescent","n","초승달","B2"),("gibbous","adj","볼록한","C2"),
("cluster","n","성단","B2"),("supercluster","n","초은하단","C2"),("filament","n","필라멘트","C2"),
("cosmicray","n","우주선","C2"),("ionize","v","이온화하다","C1"),("luminous","adj","빛나는","C1"),
("brilliance","n","광휘","C1"),("twinkle","v","반짝이다","B2"),("scintillation","n","섬광","C2"),
("aurora","n","오로라","C1"),("magnetosphere","n","자기권","C2"),("heliosphere","n","태양권","C2"),
("solarwind","n","태양풍","C2"),("cometary","adj","혜성의","C2"),("tail","n","꼬리","B2"),
("coma","n","코마","C2"),("nucleus","n","핵","C1"),("ejecta","n","분출물","C2"),
("impactor","n","충돌체","C2"),("bombardment","n","충돌세례","C1"),("catalogue","v","목록화하다","B2"),
]
for e,p,k,l in ASTRO:
    add(e,p,k,l,"천문")

# =========================================================
# GEOLOGY & EARTH SCIENCE  지구과학
# =========================================================
GEO = [
("sediment","n","퇴적물","B2"),("erosion","n","침식","B2"),("tectonic","adj","지각구조의","C1"),
("mineral","n","광물","B2"),("volcanic","adj","화산의","B2"),("strata","n","지층","C1"),
("stratum","n","지층","C1"),("stratify","v","층을 이루다","C2"),("stratification","n","성층","C2"),
("geology","n","지질학","B2"),("geological","adj","지질학의","B2"),("geologist","n","지질학자","B2"),
("plate","n","판","B2"),("fault","n","단층","B2"),("rift","n","열곡","C1"),
("subduction","n","섭입","C2"),("convergent","adj","수렴하는","C1"),("divergent","adj","발산하는","C1"),
("crust","n","지각","B2"),("mantle","n","맨틀","C1"),("magma","n","마그마","B2"),
("lava","n","용암","B2"),("molten","adj","녹은","C1"),("igneous","adj","화성의","C1"),
("sedimentary","adj","퇴적의","C1"),("metamorphic","adj","변성의","C1"),("metamorphism","n","변성작용","C2"),
("granite","n","화강암","B2"),("basalt","n","현무암","C1"),("limestone","n","석회암","B2"),
("sandstone","n","사암","C1"),("shale","n","셰일","C1"),("quartz","n","석영","B2"),
("feldspar","n","장석","C2"),("mica","n","운모","C2"),("gypsum","n","석고","C1"),
("ore","n","광석","B2"),("deposit","n","광상","B2"),("vein","n","광맥","B2"),
("outcrop","n","노두","C2"),("bedrock","n","기반암","C1"),("boulder","n","큰바위","B2"),
("gravel","n","자갈","B2"),("silt","n","미사","C1"),("clay","n","점토","B2"),
("loam","n","양토","C2"),("weathering","n","풍화","C1"),("weather","v","풍화하다","B2"),
("abrasion","n","마모","C1"),("deposition","n","퇴적","C1"),("sedimentation","n","퇴적작용","C1"),
("compaction","n","다짐","C1"),("cementation","n","고결","C2"),("lithification","n","암석화","C2"),
("fossil","n","화석","B2"),("fossilize","v","화석화하다","C1"),("paleontology","n","고생물학","C2"),
("paleontologist","n","고생물학자","C2"),("stratigraphy","n","층서학","C2"),("geochronology","n","지질연대학","C2"),
("epoch","n","세","C1"),("eon","n","누대","C2"),("era","n","대","B2"),
("period","n","기","B2"),("Precambrian","adj","선캄브리아기의","C2"),("seismic","adj","지진의","C1"),
("seismology","n","지진학","C2"),("seismograph","n","지진계","C2"),("epicenter","n","진앙","C1"),
("magnitude","n","진도","C1"),("tremor","n","진동","C1"),("aftershock","n","여진","C1"),
("earthquake","n","지진","B2"),("eruption","n","분출","B2"),("erupt","v","분출하다","B2"),
("volcano","n","화산","B2"),("caldera","n","칼데라","C2"),("crater","n","분화구","B2"),
("vent","n","분화구","B2"),("fissure","n","균열","C1"),("geyser","n","간헐천","C1"),
("hotspring","n","온천","B2"),("fumarole","n","분기공","C2"),("pyroclastic","adj","화쇄성의","C2"),
("ash","n","화산재","B2"),("pumice","n","부석","C2"),("obsidian","n","흑요석","C2"),
("plateau","n","고원","B2"),("mesa","n","메사","C2"),("canyon","n","협곡","B2"),
("ravine","n","골짜기","C1"),("gorge","n","협곡","C1"),("valley","n","계곡","B2"),
("basin","n","분지","B2"),("ridge","n","능선","B2"),("escarpment","n","급경사면","C2"),
("terrain","n","지형","B2"),("topography","n","지형학","C1"),("topographic","adj","지형의","C1"),
("relief","n","기복","C1"),("elevation","n","고도","B2"),("altitude","n","고도","B2"),
("gradient","n","경사","C1"),("slope","n","경사면","B2"),("incline","n","경사","B2"),
("landform","n","지형","C1"),("landmass","n","대륙덩어리","C1"),("continental","adj","대륙의","B2"),
("oceanic","adj","해양의","C1"),("crustal","adj","지각의","C2"),("uplift","n","융기","C1"),
("subsidence","n","침강","C2"),("orogeny","n","조산운동","C2"),("folding","n","습곡","C1"),
("fold","n","습곡","B2"),("faulting","n","단층작용","C1"),("displacement","n","변위","C1"),
("mineralogy","n","광물학","C2"),("crystalline","adj","결정질의","C1"),("crystal","n","결정","B2"),
("cleavage","n","벽개","C2"),("lustre","n","광택","C1"),("hardness","n","경도","B2"),
("streak","n","조흔색","C2"),("specimen","n","표본","B2"),("aggregate","n","골재","C1"),
("conglomerate","n","역암","C2"),("sedimentology","n","퇴적학","C2"),("provenance","n","기원지","C2"),
("aquifer","n","대수층","C1"),("groundwater","n","지하수","B2"),("permeable","adj","투수성의","C1"),
("impermeable","adj","불투수성의","C1"),("porosity","n","공극률","C2"),("porous","adj","다공성의","C1"),
("infiltration","n","침투","C1"),("percolation","n","삼투","C2"),("percolate","v","스며들다","C1"),
("karst","n","카르스트","C2"),("stalactite","n","종유석","C1"),("stalagmite","n","석순","C1"),
("cavern","n","동굴","B2"),("dissolution","n","용해","C1"),("leaching","n","용출","C2"),
("mineralize","v","광물화하다","C2"),("crystallography","n","결정학","C2"),("isostasy","n","지각평형","C2"),
("geomorphology","n","지형학","C2"),("denudation","n","삭박작용","C2"),("alluvium","n","충적층","C2"),
("alluvial","adj","충적의","C2"),("delta","n","삼각주","B2"),("floodplain","n","범람원","C1"),
("meander","n","곡류","C1"),("tributary","n","지류","C1"),("watershed","n","분수령","C1"),
("drainage","n","배수","B2"),("sediment","v","퇴적시키다","C1"),("silica","n","실리카","C1"),
("dune","n","사구","B2"),("moraine","n","빙퇴석","C2"),("till","n","빙력토","C2"),
("outwash","n","유수퇴적물","C2"),("glaciation","n","빙하작용","C1"),("glacial","adj","빙하의","C1"),
("permafrost","n","영구동토","C1"),("tundra","n","툰드라","B2"),("weathered","adj","풍화된","B2"),
]
for e,p,k,l in GEO:
    add(e,p,k,l,"지구과학")

# =========================================================
# METEOROLOGY, OCEANOGRAPHY & ENVIRONMENTAL  환경
# =========================================================
ENV = [
("atmosphere","n","대기","B2"),("precipitation","n","강수","B2"),("current","n","해류","B2"),
("glacier","n","빙하","B2"),("emission","n","배출","B2"),("pollutant","n","오염물질","B2"),
("meteorology","n","기상학","C1"),("meteorological","adj","기상의","C1"),("climate","n","기후","B2"),
("climatic","adj","기후의","C1"),("climatology","n","기후학","C2"),("weather","n","날씨","B2"),
("humidity","n","습도","B2"),("humid","adj","습한","B2"),("arid","adj","건조한","C1"),
("aridity","n","건조","C2"),("semiarid","adj","반건조의","C2"),("temperate","adj","온대의","B2"),
("tropical","adj","열대의","B2"),("subtropical","adj","아열대의","C1"),("polar","adj","극지의","B2"),
("condensation","n","응결","C1"),("evaporation","n","증발","B2"),("transpiration","n","증산","C1"),
("sublimation","n","승화","C2"),("saturation","n","포화","C1"),("dewpoint","n","이슬점","C2"),
("cloud","n","구름","B2"),("cumulus","n","적운","C1"),("cirrus","n","권운","C1"),
("stratus","n","층운","C1"),("nimbus","n","비구름","C2"),("overcast","adj","흐린","B2"),
("front","n","전선","B2"),("cyclone","n","저기압","C1"),("anticyclone","n","고기압","C2"),
("depression","n","저기압","C1"),("isobar","n","등압선","C2"),("barometer","n","기압계","B2"),
("barometric","adj","기압의","C1"),("hygrometer","n","습도계","C2"),("thermometer","n","온도계","B2"),
("anemometer","n","풍속계","C2"),("gauge","n","측정기","B2"),("forecast","n","예보","B2"),
("forecasting","n","예보","B2"),("hurricane","n","허리케인","B2"),("typhoon","n","태풍","B2"),
("tornado","n","토네이도","B2"),("gale","n","강풍","C1"),("gust","n","돌풍","C1"),
("breeze","n","산들바람","B2"),("squall","n","돌풍","C2"),("blizzard","n","눈보라","B2"),
("drought","n","가뭄","B2"),("monsoon","n","몬순","C1"),("downpour","n","폭우","C1"),
("deluge","n","호우","C2"),("sleet","n","진눈깨비","C1"),("hail","n","우박","B2"),
("frost","n","서리","B2"),("dew","n","이슬","B2"),("mist","n","엷은 안개","B2"),
("fog","n","안개","B2"),("haze","n","연무","C1"),("smog","n","스모그","B2"),
("visibility","n","시정","B2"),("turbulent","adj","난기류의","C1"),("jetstream","n","제트기류","C1"),
("windward","adj","바람부는 쪽의","C2"),("leeward","adj","바람그늘의","C2"),("prevailing","adj","탁월한","C1"),
("trade","adj","무역풍의","C1"),("updraft","n","상승기류","C2"),("downdraft","n","하강기류","C2"),
("thunderstorm","n","뇌우","B2"),("lightning","n","번개","B2"),("thunder","n","천둥","B2"),
("ozone","n","오존","B2"),("stratosphere","n","성층권","C1"),("troposphere","n","대류권","C1"),
("mesosphere","n","중간권","C2"),("thermosphere","n","열권","C2"),("ionosphere","n","전리층","C2"),
("greenhouse","adj","온실의","B2"),("warming","n","온난화","B2"),("carbon","n","탄소","B2"),
("methane","n","메탄","C1"),("dioxide","n","이산화물","B2"),("sequestration","n","격리","C2"),
("footprint","n","발자국","B2"),("mitigation","n","완화","C1"),("mitigate","v","완화하다","C1"),
("adaptation","n","적응","B2"),("resilience","n","회복력","C1"),("vulnerability","n","취약성","C1"),
("ecosystem","n","생태계","B2"),("biodiversity","n","생물다양성","C1"),("habitat","n","서식지","B2"),
("biome","n","생물군계","C1"),("ecology","n","생태학","B2"),("ecological","adj","생태학의","B2"),
("sustainability","n","지속가능성","B2"),("sustainable","adj","지속가능한","B2"),("renewable","adj","재생가능한","B2"),
("nonrenewable","adj","재생불가능한","C1"),("depletion","n","고갈","C1"),("deplete","v","고갈시키다","C1"),
("conservation","n","보존","B2"),("preserve","v","보존하다","B2"),("degradation","n","황폐화","C1"),
("degrade","v","저하시키다","C1"),("deforestation","n","삼림파괴","B2"),("desertification","n","사막화","C1"),
("reforestation","n","재조림","C1"),("afforestation","n","조림","C2"),("salinity","n","염분","C1"),
("saline","adj","염분의","C1"),("brackish","adj","기수의","C2"),("desalination","n","담수화","C1"),
("effluent","n","폐수","C2"),("runoff","n","유출수","C1"),("sewage","n","하수","B2"),
("wastewater","n","폐수","B2"),("contamination","n","오염","B2"),("contaminate","v","오염시키다","B2"),
("pollution","n","오염","B2"),("pollute","v","오염시키다","B2"),("toxin","n","독소","B2"),
("toxic","adj","독성의","B2"),("toxicity","n","독성","C1"),("carcinogen","n","발암물질","C2"),
("particulate","n","미립자","C1"),("aerosol","n","에어로졸","C1"),("emit","v","배출하다","B2"),
("discharge","n","방류","B2"),("leachate","n","침출수","C2"),("eutrophication","n","부영양화","C2"),
("algal","adj","조류의","C2"),("bloom","n","대번식","B2"),("acidification","n","산성화","C1"),
("acidrain","n","산성비","B2"),("smokestack","n","굴뚝","C1"),("scrubber","n","세정기","C2"),
("oceanography","n","해양학","C1"),("oceanic","adj","해양의","C1"),("marine","adj","해양의","B2"),
("tide","n","조수","B2"),("tidal","adj","조수의","C1"),("ebb","n","썰물","C1"),
("surge","n","해일","C1"),("swell","n","너울","B2"),("undertow","n","역류","C2"),
("upwelling","n","용승","C2"),("thermocline","n","수온약층","C2"),("salinity","adj","염도의","C1"),
("estuary","n","하구","C1"),("lagoon","n","석호","B2"),("reef","n","암초","B2"),
("coral","n","산호","B2"),("plankton","n","플랑크톤","B2"),("phytoplankton","n","식물플랑크톤","C1"),
("krill","n","크릴","C1"),("benthic","adj","저서의","C2"),("pelagic","adj","원양의","C2"),
("abyssal","adj","심해의","C2"),("continental","adj","대륙붕의","B2"),("trench","n","해구","B2"),
("seabed","n","해저","B2"),("seafloor","n","해저","C1"),("bathymetry","n","수심측량","C2"),
("submarine","adj","해저의","B2"),("hydrothermal","adj","열수의","C2"),("sedimentary","adj","퇴적성의","C1"),
("wetland","n","습지","B2"),("marsh","n","습지","B2"),("bog","n","늪","C1"),
("swamp","n","늪","B2"),("mangrove","n","맹그로브","C1"),("watershed","n","유역","C1"),
("catchment","n","집수구역","C2"),("aquatic","adj","수생의","B2"),("terrestrial","adj","육상의","C1"),
("nutrient","n","영양분","B2"),("cycle","n","순환","B2"),("biogeochemical","adj","생지화학의","C2"),
("nitrogen","adj","질소의","B2"),("carbonic","adj","탄산의","C2"),("assimilation","n","동화","C1"),
("decomposition","n","분해","C1"),("decompose","v","분해하다","C1"),("biodegradable","adj","생분해성의","C1"),
("compost","n","퇴비","B2"),("recycle","v","재활용하다","B2"),("recyclable","adj","재활용가능한","B2"),
("landfill","n","매립지","B2"),("incineration","n","소각","C1"),("incinerate","v","소각하다","C1"),
("emission","adj","배출의","B2"),("particulate","adj","미립자의","C1"),("respirable","adj","호흡성의","C2"),
("albedo","n","반사율","C2"),("insolation","n","일사량","C2"),("radiative","adj","복사의","C2"),
("microclimate","n","미기후","C1"),("phenology","n","생물계절학","C2"),("biomass","n","생물량","C1"),
("carbonsink","n","탄소흡수원","C2"),("stewardship","n","환경관리","C1"),("remediation","n","정화","C2"),
]
for e,p,k,l in ENV:
    add(e,p,k,l,"환경")

# =========================================================
# SUPPLEMENT (to reach 1000 after cross-domain dedup)
# =========================================================
SUPP = [
# astronomy (천문) — was low
("umbra","n","본영","C2","천문"),("penumbra","n","반영","C2","천문"),
("annular","adj","금환의","C2","천문"),("totality","n","개기식","C2","천문"),
("ecliptic","n","황도","C2","천문"),("spiral","adj","나선형의","B2","천문"),
("culminate","v","자오선을 통과하다","C1","천문"),("sidereal","adj","항성의","C2","천문"),
("synodic","adj","삭망의","C2","천문"),("retrograde","adj","역행의","C2","천문"),
("prograde","adj","순행의","C2","천문"),("declination","n","적위","C2","천문"),
("ephemeris","n","천체력","C2","천문"),("astrometry","n","위치천문학","C2","천문"),
("photometry","n","측광법","C2","천문"),("spectral","adj","스펙트럼의","C1","천문"),
("binary","adj","쌍성의","C1","천문"),("variable","adj","변광의","B2","천문"),
("halo","n","헤일로","C1","천문"),("bulge","n","팽대부","C1","천문"),
("disk","n","원반","B2","천문"),("interplanetary","adj","행성간의","C1","천문"),
("circumstellar","adj","항성주위의","C2","천문"),("suborbital","adj","준궤도의","C2","천문"),
("telemetry","n","원격측정","C2","천문"),("declinate","v","기울다","C2","천문"),
("luminance","n","휘도","C2","천문"),("brightening","n","증광","C1","천문"),
("dimming","n","감광","C1","천문"),("orbitally","adv","궤도상으로","C2","천문"),
("gravitationally","adv","중력적으로","C2","천문"),("cosmically","adv","우주적으로","C2","천문"),
("stellarwind","n","항성풍","C2","천문"),("nucleon","n","핵자","C2","천문"),
("recession","n","후퇴","C1","천문"),("recede","v","멀어지다","B2","천문"),
("collimate","v","평행하게하다","C2","천문"),("baseline","n","기선","C1","천문"),
("resolution","n","분해능","B2","천문"),("aperturize","v","조리개조절하다","C2","천문"),
("radiant","n","복사점","C1","천문"),("shower","n","유성우","B2","천문"),
("perturbation","n","섭동","C2","천문"),("perturb","v","교란하다","C1","천문"),
("resonate","v","공명하다","C1","천문"),("libration","n","칭동","C2","천문"),
("apparition","n","출현","C1","천문"),("elongation","n","이각","C2","천문"),
("culmination","n","남중","C2","천문"),("astral","adj","별의","C1","천문"),
# geology (지구과학)
("bedding","n","층리","C2","지구과학"),("unconformity","n","부정합","C2","지구과학"),
("dike","n","암맥","C2","지구과학"),("sill","n","암상","C2","지구과학"),
("batholith","n","저반","C2","지구과학"),("pluton","n","심성암체","C2","지구과학"),
("intrusion","n","관입","C1","지구과학"),("extrusion","n","분출","C1","지구과학"),
("intrude","v","관입하다","C1","지구과학"),("solidify","v","응고하다","B2","지구과학"),
("consolidate","v","굳어지다","B2","지구과학"),("lithosphere","n","암석권","C1","지구과학"),
("asthenosphere","n","연약권","C2","지구과학"),("hydrosphere","n","수권","C1","지구과학"),
("biosphere","n","생물권","C1","지구과학"),("geothermal","adj","지열의","C1","지구과학"),
("ductile","adj","연성의","C2","지구과학"),("brittle","adj","취성의","C1","지구과학"),
("cleave","v","쪼개지다","C1","지구과학"),("granular","adj","입상의","C1","지구과학"),
# physics (물리)
("collision","n","충돌","B2","물리"),("collide","v","충돌하다","B2","물리"),
("elasticity","adj","탄성의","C1","물리"),("recoil","n","반동","C1","물리"),
("impulse","n","충격량","C1","물리"),("restitution","n","반발","C2","물리"),
("damping","n","감쇠","C2","물리"),("modulate","v","변조하다","C1","물리"),
("modulation","n","변조","C1","물리"),("superposition","n","중첩","C2","물리"),
("coherence","n","가간섭성","C2","물리"),("wavefunction","n","파동함수","C2","물리"),
("quantize","v","양자화하다","C2","물리"),("annihilate","v","소멸시키다","C2","물리"),
# chemistry (화학)
("effuse","v","분출하다","C2","화학"),("diffuse","v","확산하다","C1","화학"),
("diffusion","n","확산","B2","화학"),("osmosis","n","삼투","C1","화학"),
("permeate","v","침투하다","C1","화학"),("sublimate","v","승화하다","C2","화학"),
("nucleate","v","핵생성하다","C2","화학"),("agglomerate","v","응집하다","C2","화학"),
# environmental (환경)
("albedic","adj","반사의","C2","환경"),("windchill","n","체감온도","C1","환경"),
("evapotranspiration","n","증발산","C2","환경"),("hydrology","n","수문학","C1","환경"),
("hydrological","adj","수문학의","C1","환경"),("biodegrade","v","생분해되다","C1","환경"),
("bioaccumulation","n","생물농축","C2","환경"),("biomagnification","n","생물확대","C2","환경"),
]
for e,p,k,l,t in SUPP:
    W.append((e,p,k,l,t))

# ---------- dedup by headword ----------
seen = {}
dedup = []
for e,p,k,l,t in W:
    key = e.lower()
    if key in seen:
        continue
    seen[key] = True
    dedup.append({"en":e.lower(),"pos":p,"ko":k,"level":l,"topic":t})

print("raw:", len(W), "after dedup:", len(dedup))

# report distribution
lv = collections.Counter(d["level"] for d in dedup)
tp = collections.Counter(d["topic"] for d in dedup)
print("levels:", dict(lv))
print("topics:", dict(tp))

# We need exactly 1000. Trim or report.
target = 1000
if len(dedup) > target:
    # trim from the largest topics to keep balance, removing lowest-priority extras
    over = len(dedup) - target
    # remove from end within most-populous topics
    # simplest balanced trim: repeatedly drop last item of the currently-largest topic
    while over > 0:
        tp2 = collections.Counter(d["topic"] for d in dedup)
        biggest = max(tp2, key=lambda x: tp2[x])
        # remove last occurrence of biggest topic
        for i in range(len(dedup)-1, -1, -1):
            if dedup[i]["topic"] == biggest:
                dedup.pop(i)
                break
        over -= 1

print("final:", len(dedup))
lv = collections.Counter(d["level"] for d in dedup)
tp = collections.Counter(d["topic"] for d in dedup)
print("final levels:", dict(lv))
print("final topics:", dict(tp))

with open("/home/user/voca/wordbooks/toefl-build/poolC.json","w",encoding="utf-8") as f:
    json.dump(dedup, f, ensure_ascii=False, indent=1)

# verify parse
with open("/home/user/voca/wordbooks/toefl-build/poolC.json","r",encoding="utf-8") as f:
    data = json.load(f)
print("parsed OK, count =", len(data))
