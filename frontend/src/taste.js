import React, { useEffect, useState } from 'react';
import { Pie } from 'react-chartjs-2';
import { Chart as ChartJS } from 'chart.js/auto';

function ArtistStatistics() {
    console.log('ArtistStatistics component rendered');
    const [genreData, setGenreData] = useState(null);

    useEffect(() => {
        console.log('useEffect hook triggered');
        fetch('http://localhost:3000/get_selected_playlists')  
            .then((response) => response.json())
            .then((data) => {
                console.log('Fetched data:', data);
                const genres = data.genres;
                const labels = Object.keys(genres);
                const values = Object.values(genres);

                setGenreData({
                    labels: labels,   
                    datasets: [
                        {
                            data: values,  
                            backgroundColor: ['#FF9999', '#66B3FF', '#99FF99', '#FFCC99', '#FF6666', '#66FF66', '#99CCFF'],
                        }
                    ]
                });
            })
            .catch((error) => console.error('Error fetching data:', error));
    }, []);

    return (
        <div>
            <h1>Genre Statistics</h1>
            <div>
                {genreData ? (
                    <Pie data={genreData} />
                ) : (
                    <p>Loading data...</p>
                )}
            </div>
        </div>
    );
}

export default ArtistStatistics;
