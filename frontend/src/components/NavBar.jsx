import React, { memo } from "react";

const NavBar = memo(({ title }) => {
    return (
        <header 
            className="fixed top-0 left-0 w-full p-4 bg-white/70 dark:bg-gray-800/70 
                backdrop-blur-md shadow-md z-10 flex justify-center items-center
                transition-colors duration-200"
            role="banner"
        >
            <h1 className="text-xl font-bold font-poppins">
                {title}
            </h1>
        </header>
    );
});

NavBar.displayName = 'NavBar';

export default NavBar;
