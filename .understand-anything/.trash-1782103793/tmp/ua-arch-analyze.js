#!/usr/bin/env node
'use strict';
const fs = require('fs');

function main() {
  const inPath = process.argv[2];
  const outPath = process.argv[3];
  if (!inPath || !outPath) {
    console.error('Usage: analyze.js <input.json> <output.json>');
    process.exit(1);
  }
  const data = JSON.parse(fs.readFileSync(inPath, 'utf8'));
  const fileNodes = data.fileNodes || [];
  const importEdges = data.importEdges || [];
  const allEdges = data.allEdges || [];

  const idToNode = {};
  fileNodes.forEach(n => { idToNode[n.id] = n; });
  const validIds = new Set(fileNodes.map(n => n.id));

  // Common prefix of file paths
  const paths = fileNodes.map(n => n.filePath);
  function commonPrefixDir(ps) {
    if (ps.length === 0) return '';
    const split = ps.map(p => p.split('/'));
    let prefix = [];
    const first = split[0];
    for (let i = 0; i < first.length - 1; i++) {
      const seg = first[i];
      if (split.every(s => s.length > i + 1 && s[i] === seg)) prefix.push(seg);
      else break;
    }
    return prefix.length ? prefix.join('/') + '/' : '';
  }
  const prefix = commonPrefixDir(paths);

  // A. Directory grouping
  const directoryGroups = {};
  fileNodes.forEach(n => {
    let rel = n.filePath;
    if (prefix && rel.startsWith(prefix)) rel = rel.slice(prefix.length);
    const parts = rel.split('/');
    const group = parts.length > 1 ? parts[0] : 'root';
    (directoryGroups[group] = directoryGroups[group] || []).push(n.id);
  });

  // B. Node type grouping
  const nodeTypeGroups = {};
  fileNodes.forEach(n => {
    (nodeTypeGroups[n.type] = nodeTypeGroups[n.type] || []).push(n.id);
  });

  // file -> group map
  const fileGroup = {};
  Object.entries(directoryGroups).forEach(([g, ids]) => ids.forEach(id => { fileGroup[id] = g; }));

  // C. Import adjacency: fan-in/out
  const fanIn = {}, fanOut = {};
  fileNodes.forEach(n => { fanIn[n.id] = 0; fanOut[n.id] = 0; });
  importEdges.forEach(e => {
    if (validIds.has(e.source)) fanOut[e.source]++;
    if (validIds.has(e.target)) fanIn[e.target]++;
  });

  // D. Cross-category edges
  const crossMap = {};
  allEdges.forEach(e => {
    const s = idToNode[e.source], t = idToNode[e.target];
    if (!s || !t) return;
    if (s.type === t.type) return;
    const key = s.type + '|' + t.type + '|' + e.type;
    crossMap[key] = (crossMap[key] || 0) + 1;
  });
  const crossCategoryEdges = Object.entries(crossMap).map(([k, count]) => {
    const [fromType, toType, edgeType] = k.split('|');
    return { fromType, toType, edgeType, count };
  });

  // E. Inter-group import frequency (from importEdges)
  const interMap = {};
  importEdges.forEach(e => {
    const fg = fileGroup[e.source], tg = fileGroup[e.target];
    if (!fg || !tg || fg === tg) return;
    const key = fg + '|' + tg;
    interMap[key] = (interMap[key] || 0) + 1;
  });
  const interGroupImports = Object.entries(interMap).map(([k, count]) => {
    const [from, to] = k.split('|');
    return { from, to, count };
  });

  // F. Intra-group density
  const intraGroupDensity = {};
  Object.keys(directoryGroups).forEach(g => {
    let internal = 0, total = 0;
    importEdges.forEach(e => {
      const fg = fileGroup[e.source], tg = fileGroup[e.target];
      if (fg === g || tg === g) {
        total++;
        if (fg === g && tg === g) internal++;
      }
    });
    intraGroupDensity[g] = { internalEdges: internal, totalEdges: total, density: total ? +(internal / total).toFixed(3) : 0 };
  });

  // G. Pattern matching
  const dirPatterns = [
    [/^(routes|api|controllers|endpoints|handlers|controller|routers|serializers|blueprints)$/, 'api'],
    [/^(services|core|lib|domain|logic|composables|signals|mailers|jobs|channels|internal)$/, 'service'],
    [/^(models|db|data|persistence|repository|entities|migrations|entity|sql|database)$/, 'data'],
    [/^(components|views|pages|ui|layouts|screens)$/, 'ui'],
    [/^(middleware|plugins|interceptors|guards)$/, 'middleware'],
    [/^(utils|helpers|common|shared|tools|templatetags|pkg)$/, 'utility'],
    [/^(config|constants|env|settings|management|commands)$/, 'config'],
    [/^(__tests__|test|tests|spec|specs)$/, 'test'],
    [/^(types|interfaces|schemas|contracts|dtos|dto|request|response)$/, 'types'],
    [/^hooks$/, 'hooks'],
    [/^(store|state|reducers|actions|slices)$/, 'state'],
    [/^(assets|static|public)$/, 'assets'],
    [/^(cmd|bin)$/, 'entry'],
    [/^(docs|documentation|wiki)$/, 'documentation'],
    [/^(deploy|deployment|infra|infrastructure|k8s|kubernetes|helm|charts|terraform|tf|docker)$/, 'infrastructure'],
    [/^(\.github|\.gitlab|\.circleci)$/, 'ci-cd'],
  ];
  function matchDir(name) {
    for (const [re, label] of dirPatterns) if (re.test(name)) return label;
    return null;
  }
  function matchFile(fp, name) {
    if (/(\.test\.|\.spec\.|_test\.go$|Test\.java$|_spec\.rb$|Test\.php$|Tests\.cs$)/.test(fp) || /^test_.*\.py$/.test(name)) return 'test';
    if (/\.d\.ts$/.test(fp)) return 'types';
    if (/Dockerfile/.test(name) || /^docker-compose\./.test(name)) return 'infrastructure';
    if (/\.(tf|tfvars)$/.test(fp)) return 'infrastructure';
    if (/\.gitlab-ci\.yml$/.test(name) || /Jenkinsfile/.test(name)) return 'ci-cd';
    if (/\.sql$/.test(fp)) return 'data';
    if (/\.(graphql|gql|proto)$/.test(fp)) return 'types';
    if (/\.(md|rst)$/.test(fp)) return 'documentation';
    if (/^Makefile$/.test(name)) return 'infrastructure';
    return null;
  }
  const patternMatches = {};
  Object.keys(directoryGroups).forEach(g => {
    const m = matchDir(g);
    if (m) patternMatches[g] = m;
  });
  const filePatternMatches = {};
  fileNodes.forEach(n => {
    const m = matchFile(n.filePath, n.name);
    if (m) filePatternMatches[n.id] = m;
  });

  // H. Deployment topology
  const infraFiles = [];
  let hasDockerfile = false, hasCompose = false, hasK8s = false, hasTerraform = false, hasCI = false;
  fileNodes.forEach(n => {
    const nm = n.name, fp = n.filePath;
    if (/Dockerfile/.test(nm)) { hasDockerfile = true; infraFiles.push(fp); }
    if (/^docker-compose/.test(nm)) { hasCompose = true; infraFiles.push(fp); }
    if (/\.(tf|tfvars)$/.test(fp)) { hasTerraform = true; infraFiles.push(fp); }
    if (/(k8s|kubernetes|helm)/.test(fp)) { hasK8s = true; infraFiles.push(fp); }
    if (/(\.github\/workflows|\.gitlab-ci|Jenkinsfile)/.test(fp)) { hasCI = true; infraFiles.push(fp); }
  });
  const deploymentTopology = { hasDockerfile, hasCompose, hasK8s, hasTerraform, hasCI, infraFiles };

  // I. Data pipeline
  const dataPipeline = {
    schemaFiles: fileNodes.filter(n => /\.(sql|graphql|gql|proto|prisma)$/.test(n.filePath)).map(n => n.filePath),
    migrationFiles: fileNodes.filter(n => /migrations?\//.test(n.filePath)).map(n => n.filePath),
    dataModelFiles: fileNodes.filter(n => /(models?|entities|entity)\//.test(n.filePath)).map(n => n.filePath),
    apiHandlerFiles: fileNodes.filter(n => (n.tags || []).includes('api-handler') || /(routes|controllers|handlers|api)\//.test(n.filePath)).map(n => n.filePath),
  };

  // J. Doc coverage
  const groups = Object.keys(directoryGroups);
  const groupsWithDocsSet = new Set();
  fileNodes.forEach(n => {
    if (/\.(md|rst)$/.test(n.filePath) || /readme/i.test(n.name)) {
      const g = fileGroup[n.id];
      if (g) groupsWithDocsSet.add(g);
    }
  });
  const docCoverage = {
    groupsWithDocs: groupsWithDocsSet.size,
    totalGroups: groups.length,
    coverageRatio: groups.length ? +(groupsWithDocsSet.size / groups.length).toFixed(2) : 0,
    undocumentedGroups: groups.filter(g => !groupsWithDocsSet.has(g)),
  };

  // K. Dependency direction
  const pairDir = {};
  interGroupImports.forEach(({ from, to, count }) => {
    pairDir[from + '|' + to] = count;
  });
  const seen = new Set();
  const dependencyDirection = [];
  interGroupImports.forEach(({ from, to }) => {
    const a = from, b = to;
    const key = [a, b].sort().join('|');
    if (seen.has(key)) return;
    seen.add(key);
    const ab = pairDir[a + '|' + b] || 0;
    const ba = pairDir[b + '|' + a] || 0;
    if (ab >= ba) dependencyDirection.push({ dependent: a, dependsOn: b });
    else dependencyDirection.push({ dependent: b, dependsOn: a });
  });

  const filesPerGroup = {};
  Object.entries(directoryGroups).forEach(([g, ids]) => { filesPerGroup[g] = ids.length; });
  const nodeTypeCounts = {};
  Object.entries(nodeTypeGroups).forEach(([t, ids]) => { nodeTypeCounts[t] = ids.length; });

  const result = {
    scriptCompleted: true,
    commonPrefix: prefix,
    directoryGroups,
    nodeTypeGroups,
    crossCategoryEdges,
    interGroupImports,
    intraGroupDensity,
    patternMatches,
    filePatternMatches,
    deploymentTopology,
    dataPipeline,
    docCoverage,
    dependencyDirection,
    fileStats: { totalFileNodes: fileNodes.length, filesPerGroup, nodeTypeCounts },
    fileFanIn: fanIn,
    fileFanOut: fanOut,
  };
  fs.writeFileSync(outPath, JSON.stringify(result, null, 2));
}

try { main(); } catch (e) { console.error(e.stack || String(e)); process.exit(1); }
