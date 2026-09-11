import React from 'react';

export function NetworkGraphic() {
  return (
    <div className="network-topology" aria-hidden="true">
      <div className="topo-node scanning-pulse">
        <span className="topo-label">Edge router</span>
      </div>
      <div className="topo-node">
        <span className="topo-label">Branch switch</span>
      </div>
      <div className="topo-node">
        <span className="topo-label">Core firewall</span>
      </div>
      <div className="topo-node scanning-pulse" style={{ animationDelay: '1s' }}>
        <span className="topo-label">Wireless controller</span>
      </div>
      <div className="topo-node">
        <span className="topo-label">Virtual gateway</span>
      </div>
    </div>
  );
}
