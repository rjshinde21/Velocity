import img1 from "../assets/carousel1.png";
import img2 from "../assets/carousel2.png"
import img3 from "../assets/carousel3.png"
import img4 from "../assets/carousel4.png"
import img5 from "../assets/carousel5.png"
import img6 from "../assets/carousel6.png"


const Carousel = ({speed}) => {

  const images = [
   img1, img2, img3, img4, img5, img6
  ].map((image) => ({
    id: crypto.randomUUID(),
    image
  }));

  return (
    <>
      <div className="sm:w-[80%] w-full">
        <h1 className="bg-gradient-text pt-20 sm:pt-60 text-3xl sm:text-5xl mb-12 w-[90%] sm:w-[60%] mx-auto font-[Amenti]">
          At Velocity — We craft AI driven prompts that engage your audience
          with clarity and creativity.
        </h1>
      </div>

      {/* Backward scrolling section */}
      <div className="inner1 overflow-hidden">
        <div className="wrapper row1">
          <section style={{ "--speed": `${speed}ms` }}>
            {images.map(({ id, image }) => (
              <div className="image" key={id}>
                <img src={image} alt={id} />
              </div>
            ))}
          </section>
          <section style={{ "--speed": `${speed}ms` }}>
            {images.map(({ id, image }) => (
              <div className="image" key={id}>
                <img src={image} alt={id} />
              </div>
            ))}
          </section>
          <section style={{ "--speed": `${speed}ms` }}>
            {images.map(({ id, image }) => (
              <div className="image" key={id}>
                <img src={image} alt={id} />
              </div>
            ))}
          </section>
        </div>
      </div>

      {/* Forward scrolling section */}
      <div className="inner1 overflow-hidden">
        <div className="wrapper row2">
          <section style={{ "--speed": `${speed}ms` }}>
            {images.map(({ id, image }) => (
              <div className="image" key={id}>
                <img src={image} alt={id} />
              </div>
            ))}
          </section>
          <section style={{ "--speed": `${speed}ms` }}>
            {images.map(({ id, image }) => (
              <div className="image" key={id}>
                <img src={image} alt={id} />
              </div>
            ))}
          </section>
          <section style={{ "--speed": `${speed}ms` }}>
            {images.map(({ id, image }) => (
              <div className="image" key={id}>
                <img src={image} alt={id} />
              </div>
            ))}
          </section>
        </div>
      </div>
    </>
  );
};

export default Carousel;
