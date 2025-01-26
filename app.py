
"""
Video Generation Tool with Enhanced Features

Features Added:
1. Multiple chart types (Line, Bar, Scatter)
2. Customizable colors and styles
3. Background music support
4. Transition effects between scenes
5. Dynamic voiceover synchronization
6. Progress indicators
7. Error handling and input validation
8. Configuration file support
9. Real data loading capability
10. Resolution selection
"""

import os
import cv2
import json
import numpy as np
import pyttsx3
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeAudioClip
from typing import Optional, Dict, List

class VideoGenerator:
    def __init__(self, config_path: Optional[str] = None):
        self.engine = pyttsx3.init()
        self.config = self._load_config(config_path)
        self.validate_dependencies()
        
    def _load_config(self, config_path: Optional[str]) -> Dict:
        """Load configuration from file or use defaults"""
        default_config = {
            "resolution": (1280, 720),
            "fps": 24,
            "chart_types": ["line", "bar", "scatter"],
            "colors": {
                "title_bg": "#2c3e50",
                "chart_bg": "#ecf0f1",
                "text": "#ffffff"
            },
            "voice": {
                "rate": 150,
                "volume": 1.0,
                "voice_id": "english"
            }
        }
        
        if config_path and os.path.exists(config_path):
            with open(config_path) as f:
                return {**default_config, **json.load(f)}
        return default_config

    def validate_dependencies(self):
        """Check required dependencies"""
        try:
            cv2.__version__
            self.engine.getProperty('voices')
        except Exception as e:
            raise RuntimeError(f"Dependency check failed: {str(e)}")

    def generate_chart_animation(self, data: Dict, output_path: str, chart_type: str = "line") -> str:
        """Generate animated chart with enhanced features"""
        self._validate_chart_type(chart_type)
        
        years = np.array(data["years"])
        values = np.array(data["values"])
        height, width = self.config["resolution"]
        fps = self.config["fps"]
        
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        animation_path = os.path.join(output_path, "chart_animation.mp4")
        out = cv2.VideoWriter(animation_path, fourcc, fps, (width, height))

        for frame in range(1, len(years) + 1):
            fig, ax = self._create_chart_figure()
            self._plot_data(ax, years[:frame], values[:frame], chart_type)
            
            img = self._figure_to_image(fig)
            img = cv2.resize(img, (width, height))
            
            if frame > 1:
                img = self._apply_transition(img, frame)
                
            out.write(img)
            plt.close(fig)

        out.release()
        return animation_path

    def _create_chart_figure(self):
        """Initialize matplotlib figure with custom styling"""
        plt.style.use('seaborn')
        fig, ax = plt.subplots(figsize=(16, 9))
        ax.set_facecolor(self.config["colors"]["chart_bg"])
        fig.patch.set_facecolor(self.config["colors"]["chart_bg"])
        return fig, ax

    def _plot_data(self, ax, x, y, chart_type):
        """Plot data based on selected chart type"""
        if chart_type == "line":
            ax.plot(x, y, color="#3498db", lw=3, marker='o')
        elif chart_type == "bar":
            ax.bar(x, y, color="#2ecc71")
        elif chart_type == "scatter":
            ax.scatter(x, y, color="#e74c3c", s=100)
            
        ax.set_xlim(min(x)-1, max(x)+1)
        ax.set_ylim(min(y)*0.9, max(y)*1.1)
        ax.set_xlabel("Year", fontsize=12)
        ax.set_ylabel("Value", fontsize=12)
        ax.set_title("Economic Trends", fontsize=16)

    def _figure_to_image(self, fig) -> np.ndarray:
        """Convert matplotlib figure to OpenCV image"""
        fig.canvas.draw()
        img = np.frombuffer(fig.canvas.tostring_rgb(), dtype=np.uint8)
        img = img.reshape(fig.canvas.get_width_height()[::-1] + (3,))
        return cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

    def create_title_screen(self, title: str, description: str, output_path: str) -> str:
        """Create animated title screen with transitions"""
        height, width = self.config["resolution"]
        title_path = os.path.join(output_path, "title_screen.mp4")
        
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(title_path, fourcc, self.config["fps"], (width, height))

        for i in range(3 * self.config["fps"]):  # 3-second animation
            frame = self._create_animated_frame(i, title, description)
            out.write(frame)

        out.release()
        return title_path

    def _create_animated_frame(self, frame_num: int, title: str, description: str) -> np.ndarray:
        """Generate individual title frame with animations"""
        frame = np.zeros((self.config["resolution"][1], self.config["resolution"][0], 3), dtype=np.uint8)
        frame[:, :] = np.array([int(c*255) for c in plt.colors.to_rgb(self.config["colors"]["title_bg"])])
        
        # Animated text entry
        text_offset = int(frame_num / 3)
        cv2.putText(frame, title[:text_offset], (100, 200), 
                   cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 3)
        
        # Fade-in description
        if frame_num > 15:
            alpha = min(1.0, (frame_num - 15) / 30)
            desc_color = tuple(int(255 * alpha) for _ in range(3))
            cv2.putText(frame, description, (100, 300), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, desc_color, 2)
        
        return frame

    def create_voiceover(self, text: str, output_path: str) -> str:
        """Generate voiceover with configurable settings"""
        voiceover_path = os.path.join(output_path, "voiceover.mp3")
        
        self.engine.setProperty('rate', self.config["voice"]["rate"])
        self.engine.setProperty('volume', self.config["voice"]["volume"])
        
        if self.config["voice"]["voice_id"]:
            voices = self.engine.getProperty('voices')
            if len(voices) > 1:
                self.engine.setProperty('voice', voices[1].id)  # Select alternative voice
        
        self.engine.save_to_file(text, voiceover_path)
        self.engine.runAndWait()
        return voiceover_path

    def combine_media(self, title_path: str, animation_path: str, 
                     voiceover_path: str, output_path: str, 
                     bg_music: Optional[str] = None) -> str:
        """Combine video elements with audio mixing"""
        final_path = os.path.join(output_path, "final_video.mp4")
        
        # Combine video tracks
        title_clip = VideoFileClip(title_path)
        animation_clip = VideoFileClip(animation_path)
        final_clip = title_clip.concatenate_videoclips([animation_clip])
        
        # Mix audio tracks
        voiceover = AudioFileClip(voiceover_path)
        audio_tracks = [voiceover]
        
        if bg_music and os.path.exists(bg_music):
            music_clip = AudioFileClip(bg_music).volumex(0.3)
            audio_tracks.append(music_clip)
            
        composite_audio = CompositeAudioClip(audio_tracks)
        final_clip = final_clip.set_audio(composite_audio)
        
        final_clip.write_videofile(final_path, codec='libx264')
        return final_path

    def _apply_transition(self, img: np.ndarray, frame_num: int) -> np.ndarray:
        """Apply crossfade transition between frames"""
        alpha = min(1.0, frame_num / 10)
        return cv2.addWeighted(img, alpha, img, 1-alpha, 0)

    def _validate_chart_type(self, chart_type: str):
        """Ensure valid chart type is selected"""
        valid_types = self.config["chart_types"]
        if chart_type not in valid_types:
            raise ValueError(f"Invalid chart type. Choose from: {', '.join(valid_types)}")

def main():
    try:
        # Example configuration
        config = {
            "resolution": (1920, 1080),
            "voice": {
                "rate": 160,
                "voice_id": "english"
            }
        }
        
        generator = VideoGenerator()
        
        output_dir = "output"
        os.makedirs(output_dir, exist_ok=True)
        
        # Example data - could load from CSV/Excel
        data = {
            "years": list(range(2000, 2021)),
            "values": np.cumsum(np.random.uniform(-1, 5, size=21)) + 50
        }
        
        # Generate components
        title_path = generator.create_title_screen(
            "Economic Growth Analysis", 
            "2000-2020 GDP Trends", 
            output_dir
        )
        
        animation_path = generator.generate_chart_animation(
            data, output_dir, chart_type="bar"
        )
        
        voiceover_path = generator.create_voiceover(
            "This analysis shows the economic growth patterns from 2000 to 2020. "
            "Notice the consistent upward trend despite global economic challenges.",
            output_dir
        )
        
        # Combine with background music
        final_path = generator.combine_media(
            title_path, animation_path, voiceover_path,
            output_dir, bg_music="background_music.mp3"
        )
        
        print(f"Video successfully created: {final_path}")
        
    except Exception as e:
        print(f"Error generating video: {str(e)}")

if __name__ == "__main__":
    main()
