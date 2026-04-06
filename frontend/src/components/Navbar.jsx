import { Link } from 'react-router-dom';

function Navbar() {
  return (
    <nav style={styles.nav}>
      <Link to="/" style={styles.brand}>⚡ India EV Compare</Link>
      <div style={styles.links}>
        <Link to="/browse" style={styles.link}>Browse</Link>
        <Link to="/compare" style={styles.link}>Compare</Link>
        <Link to="/recommend" style={styles.link}>Recommend</Link>
        <Link to="/chat" style={styles.link}>💬 Chat</Link>
      </div>
    </nav>
  );
}

const styles = {
  nav: {
    display: 'flex', justifyContent: 'space-between',
    alignItems: 'center', padding: '1rem 2rem',
    backgroundColor: '#1a1a2e', color: 'white',
  },
  brand: {
    color: '#00d4ff', fontWeight: 'bold',
    fontSize: '1.4rem', textDecoration: 'none',
  },
  links: { display: 'flex', gap: '2rem' },
  link: { color: 'white', textDecoration: 'none', fontSize: '1rem' },
};

export default Navbar;